# backend/run_content_update.py

import os
import sys
import json
from services.ghl_client import update_single_custom_value, _load_json

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

# !!! IMPORTANTE: Defina aqui o ID da sub-conta que você quer atualizar.
# Este deve ser um dos IDs de localização que seu app tem permissão para acessar.
TARGET_LOCATION_ID = "HpZL025bTBTGqi2AvbTf" # Use o ID da sua sub-conta aqui!

# --- Caminhos para os arquivos de conteúdo ---
# O script espera que estes arquivos estejam na pasta raiz do projeto.
BASE_COMPLETA_PATH = os.path.join(os.path.dirname(__file__), "..", "base_completa.md")
BASE_RESUMIDA_PATH = os.path.join(os.path.dirname(__file__), "..", "base_resumida.md")

# --- Nomes dos Valores Personalizados no GoHighLevel ---
# Você pode escolher os nomes que fizerem mais sentido.
CUSTOM_VALUE_NAME_COMPLETA = "jardins_base_completa"
CUSTOM_VALUE_NAME_RESUMIDA = "jardins_base_resumida"

# --- Caminho para os dados dos tokens ---
LOCATIONS_DATA_FILE = os.path.join(os.path.dirname(__file__), "installed_locations_data.json")

# ==============================================================================
# LÓGICA PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    print("=== Iniciando Script de Atualização de Conteúdo para GoHighLevel ===")

    # 1. Ler o conteúdo dos arquivos Markdown locais
    try:
        with open(BASE_COMPLETA_PATH, "r", encoding="utf-8") as f:
            conteudo_completo = f.read()
        print(f"-> Arquivo '{BASE_COMPLETA_PATH}' lido com sucesso ({len(conteudo_completo)} caracteres).")

        with open(BASE_RESUMIDA_PATH, "r", encoding="utf-8") as f:
            conteudo_resumido = f.read()
        print(f"-> Arquivo '{BASE_RESUMIDA_PATH}' lido com sucesso ({len(conteudo_resumido)} caracteres).")
    except FileNotFoundError as e:
        print(f"!!! ERRO CRÍTICO: Arquivo de conteúdo não encontrado: {e}. Verifique os caminhos.")
        sys.exit(1)

    # 2. Encontrar o token de acesso para a localização alvo
    print(f"\nBuscando token de acesso para a Location ID: {TARGET_LOCATION_ID}...")
    locations_data = _load_json(LOCATIONS_DATA_FILE)
    access_token = None

    if locations_data and "locations" in locations_data:
        for loc in locations_data["locations"]:
            if loc.get("_id") == TARGET_LOCATION_ID or loc.get("id") == TARGET_LOCATION_ID:
                token_data = loc.get("location_specific_token_data", {})
                access_token = token_data.get("access_token")
                break
    
    if not access_token:
        print(f"!!! ERRO CRÍTICO: Não foi possível encontrar um access_token para a Location ID '{TARGET_LOCATION_ID}'.")
        print("    Certifique-se de que o script 'update_all_tokens.py' foi executado com sucesso e que esta localização instalou o app.")
        sys.exit(1)
    
    print("-> Token de acesso encontrado com sucesso!")

    # 3. Chamar a função de atualização para cada arquivo
    sucesso_completa = update_single_custom_value(
        location_id=TARGET_LOCATION_ID,
        access_token=access_token,
        custom_value_name=CUSTOM_VALUE_NAME_COMPLETA,
        new_content=conteudo_completo
    )

    sucesso_resumida = update_single_custom_value(
        location_id=TARGET_LOCATION_ID,
        access_token=access_token,
        custom_value_name=CUSTOM_VALUE_NAME_RESUMIDA,
        new_content=conteudo_resumido
    )

    # 4. Finalizar
    if sucesso_completa and sucesso_resumida:
        print("\n=== Script concluído com SUCESSO! Ambos os valores personalizados foram atualizados. ===")
    else:
        print("\n=== Script concluído com FALHAS. Verifique os logs de erro acima. ===")