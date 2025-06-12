# backend/services/ghl_client.py

import os
import json
import time
import requests
from typing import Optional
from dotenv import load_dotenv

# ==============================================================================
# 1. CONFIGURAÇÃO INICIAL
# ==============================================================================

# Carrega as variáveis de ambiente do arquivo .env na pasta 'backend/'
# É crucial que esta linha venha antes de usar os.getenv()
load_dotenv()

# --- Constantes da API ---
API_BASE_URL = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"

# --- Caminhos dos Arquivos de Dados ---
# Usar os.path.join garante que funcione em qualquer sistema operacional (Windows, Linux, Mac)
# os.path.dirname(__file__) se refere ao diretório atual (services)
# ".." sobe um nível para a pasta 'backend'
AGENCY_TOKEN_FILE   = os.path.join(os.path.dirname(__file__), "..", "gohighlevel_token.json")
LOCATIONS_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "installed_locations_data.json")

# --- Carregamento Seguro das Credenciais do .env ---
AGENCY_COMPANY_ID     = os.getenv("AGENCY_COMPANY_ID", "").strip()
APP_ID                = os.getenv("APP_ID", "").strip()
REFRESH_CLIENT_ID     = os.getenv("REFRESH_CLIENT_ID", "").strip()
REFRESH_CLIENT_SECRET = os.getenv("REFRESH_CLIENT_SECRET", "").strip()

# ==============================================================================
# 2. FUNÇÕES AUXILIARES (HELPERS)
# ==============================================================================

def _load_json(path: str) -> Optional[dict]:
    """
    Função segura para ler um arquivo JSON do disco.
    Retorna None se o arquivo não for encontrado ou se contiver um erro de formato.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"!!! [GHL] ERRO: Arquivo JSON inválido ou corrompido em: {path}")
        return None

def _save_json(path: str, data: dict) -> None:
    """
    Função para salvar um dicionário como um arquivo JSON formatado no disco.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ==============================================================================
# 3. FUNÇÕES PRINCIPAIS DE INTERAÇÃO COM A API
# ==============================================================================

def refresh_agency_token() -> bool:
    """
    Usa o 'refresh_token' do token de Agência para obter um novo 'access_token'.
    Esta função é a chave para manter a autenticação principal sempre ativa.
    """
    token_data = _load_json(AGENCY_TOKEN_FILE)
    if not token_data or "refresh_token" not in token_data:
        print(f"!!! [GHL] ERRO CRÍTICO: Arquivo de token da agência '{AGENCY_TOKEN_FILE}' não encontrado ou não contém um 'refresh_token'.")
        print(">>> SOLUÇÃO: Execute o fluxo de autorização manual (com Postman/cURL) uma vez para gerar este arquivo.")
        return False

    payload = {
        "grant_type": "refresh_token",
        "client_id": REFRESH_CLIENT_ID,
        "client_secret": REFRESH_CLIENT_SECRET,
        "refresh_token": token_data["refresh_token"],
        "user_type": token_data.get("userType", "Company")
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

    try:
        resp = requests.post(f"{API_BASE_URL}/oauth/token", data=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        new_token_data = resp.json()
        
        timestamp = int(time.time())
        new_token_data["refreshed_at_unix_timestamp"] = timestamp
        new_token_data["refreshed_at_readable"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        new_token_data["companyId"] = new_token_data.get("companyId", token_data.get("companyId"))
        new_token_data["userType"]  = new_token_data.get("userType", token_data.get("userType"))

        _save_json(AGENCY_TOKEN_FILE, new_token_data)
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [GHL] ERRO HTTP ao tentar dar refresh no token da agência: {http_err}")
        print(f"    Detalhes da resposta: {resp.text}")
        return False
    except Exception as e:
        print(f"!!! [GHL] Erro inesperado em refresh_agency_token: {e}")
        return False

def get_installed_locations() -> bool:
    """
    Usa o 'access_token' da Agência para buscar uma lista de todas as 
    sub-contas (locations) que instalaram este aplicativo.
    """
    token_json = _load_json(AGENCY_TOKEN_FILE)
    if not token_json or "access_token" not in token_json:
        print(f"!!! [GHL] ERRO: Não foi possível carregar o token da agência para buscar as localizações.")
        return False

    if not AGENCY_COMPANY_ID or not APP_ID:
        print("!!! [GHL] ERRO: As variáveis AGENCY_COMPANY_ID ou APP_ID não estão definidas no arquivo .env.")
        return False

    headers = {
        "Authorization": f"Bearer {token_json['access_token']}",
        "Version": API_VERSION, "Accept": "application/json"
    }
    params = {"isInstalled": "true", "companyId": AGENCY_COMPANY_ID, "appId": APP_ID}

    try:
        resp = requests.get(f"{API_BASE_URL}/oauth/installedLocations", headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        locations_list = data.get("locations", []) if isinstance(data, dict) else data
        _save_json(LOCATIONS_DATA_FILE, {"locations": locations_list})
        print(f">>> [GHL] {len(locations_list)} localização(ões) instalada(s) encontrada(s).")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [GHL] ERRO HTTP ao buscar localizações instaladas: {http_err}")
        print(f"    Detalhes da resposta: {resp.text}")
        return False
    except Exception as e:
        print(f"!!! [GHL] Erro inesperado em get_installed_locations: {e}")
        return False

def manage_location_tokens() -> bool:
    """
    Para cada localização encontrada, solicita um token de acesso específico para ela.
    """
    agency_token_json = _load_json(AGENCY_TOKEN_FILE)
    if not agency_token_json or "access_token" not in agency_token_json:
        print(f"!!! [GHL] ERRO: Não foi possível carregar o token da agência para gerenciar os tokens de localização.")
        return False

    locations_data = _load_json(LOCATIONS_DATA_FILE)
    if not locations_data or "locations" not in locations_data:
        print(f"!!! [GHL] ERRO: Arquivo de dados das localizações '{LOCATIONS_DATA_FILE}' não encontrado ou inválido.")
        return False

    headers = {
        "Authorization": f"Bearer {agency_token_json['access_token']}",
        "Version": API_VERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    updated_locations = []
    for loc in locations_data.get("locations", []):
        location_id = loc.get("_id") or loc.get("id")
        if not location_id:
            loc["location_specific_token_data"] = {"error": "ID da localização não encontrado no objeto"}
            updated_locations.append(loc)
            continue

        payload = {"companyId": AGENCY_COMPANY_ID, "locationId": location_id}

        try:
            resp = requests.post(f"{API_BASE_URL}/oauth/locationToken", data=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            loc["location_specific_token_data"] = resp.json()
        except requests.exceptions.HTTPError as http_err:
            loc["location_specific_token_data"] = {"error": str(http_err), "status_code": resp.status_code, "details": resp.text}
            print(f"    !!! [GHL] ERRO HTTP ao obter token para Location {location_id}: Status {resp.status_code}")
        except Exception as e:
            loc["location_specific_token_data"] = {"error": str(e)}
            print(f"    !!! [GHL] Erro inesperado para Location {location_id}: {e}")
        
        updated_locations.append(loc)

    _save_json(LOCATIONS_DATA_FILE, {"locations": updated_locations})
    return True

# ==============================================================================
# 4. FUNÇÕES DE LÓGICA DE NEGÓCIO
# ==============================================================================

def update_single_custom_value(location_id: str, access_token: str, custom_value_name: str, new_content: str) -> bool:
    """
    Cria ou atualiza um "Valor Personalizado" (Custom Value) em uma localização específica.
    """
    print(f"\n--- [GHL] Iniciando atualização do Valor Personalizado '{custom_value_name}' para a Location ID: {location_id} ---")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    list_url = f"{API_BASE_URL}/locations/{location_id}/customValues"
    existing_value_id = None
    
    try:
        resp = requests.get(list_url, headers=headers, timeout=20)
        resp.raise_for_status()
        existing_values = resp.json().get("customValues", [])
        
        for value in existing_values:
            if value.get("name") == custom_value_name:
                existing_value_id = value.get("id")
                print(f"    -> Valor Personalizado '{custom_value_name}' já existe com ID: {existing_value_id}. Será atualizado.")
                break
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [GHL] ERRO HTTP ao listar Valores Personalizados: {http_err}")
        print(f"    Detalhes: {resp.text}")
        return False
    except Exception as e:
        print(f"!!! [GHL] Erro inesperado ao listar Valores Personalizados: {e}")
        return False

    try:
        if existing_value_id:
            update_url = f"{API_BASE_URL}/locations/{location_id}/customValues/{existing_value_id}"
            
            # <<< CORREÇÃO APLICADA AQUI >>>
            # Adicionamos o 'name' ao payload, pois a API do GHL exige este campo mesmo na atualização (PUT).
            payload = {"name": custom_value_name, "value": new_content}
            
            resp = requests.put(update_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            print(f"    <- [GHL] SUCESSO: Valor Personalizado '{custom_value_name}' atualizado.")
        else:
            create_url = f"{API_BASE_URL}/locations/{location_id}/customValues"
            payload = {"name": custom_value_name, "value": new_content}
            resp = requests.post(create_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            print(f"    <- [GHL] SUCESSO: Valor Personalizado '{custom_value_name}' criado.")
        
        return True
    
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [GHL] ERRO HTTP ao salvar o Valor Personalizado: {http_err}")
        print(f"    Detalhes: {resp.text}")
        return False
    except Exception as e:
        print(f"!!! [GHL] Erro inesperado ao salvar o Valor Personalizado: {e}")
        return False