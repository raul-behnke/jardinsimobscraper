import time
import subprocess
import os
import sys

# Importa as funções que você já tem
from services.ghl_client import refresh_agency_token, get_installed_locations, manage_location_tokens, update_single_custom_value, _load_json

# ==============================================================================
# CONFIGURAÇÃO (a mesma do seu run_content_update.py)
# ==============================================================================
TARGET_LOCATION_ID = "HpZL025bTBTGqi2AvbTf"
BASE_COMPLETA_PATH = os.path.join(os.path.dirname(__file__), "..", "base_completa.md")
BASE_RESUMIDA_PATH = os.path.join(os.path.dirname(__file__), "..", "base_resumida.md")
CUSTOM_VALUE_NAME_COMPLETA = "jardins_base_completa"
CUSTOM_VALUE_NAME_RESUMIDA = "jardins_base_resumida"
LOCATIONS_DATA_FILE = os.path.join(os.path.dirname(__file__), "installed_locations_data.json")

# ==============================================================================
# FUNÇÃO PARA EXECUTAR COMANDOS NODE.JS
# ==============================================================================
def run_node_script(script_name):
    """Executa um script Node.js e verifica por erros."""
    print(f"\n--- EXECUTANDO SCRIPT NODE.JS: {script_name} ---")
    try:
        # Usamos 'node' pois estará no PATH do nosso container Docker
        process = subprocess.run(["node", script_name], check=True, capture_output=True, text=True)
        print(process.stdout)
        print(f">>> SUCESSO: {script_name} concluído.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"!!! FALHA CRÍTICA ao executar {script_name}:")
        print(e.stderr)
        return False

# ==============================================================================
# LÓGICA PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print(f"====== INICIANDO PROCESSO COMPLETO DE ATUALIZAÇÃO JARDINS GHL ({time.strftime('%Y-%m-%d %H:%M:%S')}) ======")

    # ETAPA 1: Gerar os dados mais recentes a partir do XML
    if not run_node_script("index.js"): sys.exit(1)
    if not run_node_script("categorize.js"): sys.exit(1)
    if not run_node_script("generate_knowledge_bases.js"): sys.exit(1)
    
    # ETAPA 2: Atualizar todos os tokens do GoHighLevel
    print("\n--- ATUALIZANDO TOKENS GHL ---")
    if not refresh_agency_token() or not get_installed_locations() or not manage_location_tokens():
        print("!!! FALHA CRÍTICA na atualização de tokens GHL. Abortando.")
        sys.exit(1)
    print(">>> SUCESSO: Todos os tokens GHL foram atualizados.")

    # ETAPA 3: Ler os arquivos .md gerados
    print("\n--- LENDO BASES DE CONHECIMENTO GERADAS ---")
    try:
        with open(BASE_COMPLETA_PATH, "r", encoding="utf-8") as f:
            conteudo_completo = f.read()
        with open(BASE_RESUMIDA_PATH, "r", encoding="utf-8") as f:
            conteudo_resumido = f.read()
        print(">>> SUCESSO: Arquivos .md lidos.")
    except FileNotFoundError as e:
        print(f"!!! ERRO CRÍTICO: Arquivo .md não encontrado: {e}.")
        sys.exit(1)

    # ETAPA 4: Obter o token de acesso específico para a localização alvo
    print(f"\n--- BUSCANDO TOKEN PARA LOCATION {TARGET_LOCATION_ID} ---")
    locations_data = _load_json(LOCATIONS_DATA_FILE)
    access_token = None
    if locations_data and "locations" in locations_data:
        for loc in locations_data["locations"]:
            if loc.get("_id") == TARGET_LOCATION_ID:
                access_token = loc.get("location_specific_token_data", {}).get("access_token")
                break
    if not access_token:
        print(f"!!! ERRO CRÍTICO: Token para a location alvo não encontrado.")
        sys.exit(1)
    print(">>> SUCESSO: Token da location alvo encontrado.")

    # ETAPA 5: Enviar o conteúdo para o GoHighLevel
    print("\n--- ENVIANDO CONTEÚDO PARA OS VALORES PERSONALIZADOS GHL ---")
    sucesso_completa = update_single_custom_value(TARGET_LOCATION_ID, access_token, CUSTOM_VALUE_NAME_COMPLETA, conteudo_completo)
    sucesso_resumida = update_single_custom_value(TARGET_LOCATION_ID, access_token, CUSTOM_VALUE_NAME_RESUMIDA, conteudo_resumido)

    if sucesso_completa and sucesso_resumida:
        print(f"\n====== PROCESSO FINALIZADO COM SUCESSO ({time.strftime('%Y-%m-%d %H:%M:%S')}) ======")
    else:
        print(f"\n====== PROCESSO FINALIZADO COM FALHAS ({time.strftime('%Y-%m-%d %H:%M:%S')}) ======")
        sys.exit(1)