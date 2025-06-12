# backend/update_all_tokens.py

import time
from services.ghl_client import refresh_agency_token, get_installed_locations, manage_location_tokens

if __name__ == "__main__":
    """
    Este script é o ponto de entrada principal para a atualização de tokens.
    Ele deve ser executado periodicamente (ex: via CRON Job) para manter
    todos os tokens do GoHighLevel atualizados.
    """
    print(f"=== Iniciando Update Completo de Tokens ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")

    # ETAPA 1: Atualizar o token principal da Agência.
    # Esta é a etapa mais importante. Sem um token de agência válido,
    # as outras etapas não podem ser executadas.
    print("\n--- ETAPA 1: Atualizando o token da Agência ---")
    if not refresh_agency_token():
        print("\n>>> FALHA CRÍTICA no refresh do token da agência. O script será encerrado.")
        exit(1)
    print(">>> SUCESSO: Token da agência atualizado.")


    # ETAPA 2: Buscar a lista de todas as localizações que instalaram o app.
    # Usa o token de agência recém-atualizado para obter a lista.
    print("\n--- ETAPA 2: Buscando as localizações instaladas ---")
    if not get_installed_locations():
        print("\n>>> FALHA ao obter as localizações instaladas. Verifique os logs.")
        exit(1)
    print(">>> SUCESSO: Lista de localizações obtida.")


    # ETAPA 3: Obter um token de acesso específico para cada localização.
    # Itera sobre a lista da Etapa 2 e solicita um token para cada uma.
    print("\n--- ETAPA 3: Gerenciando os tokens de cada localização ---")
    if not manage_location_tokens():
        print("\n>>> FALHA ao obter os tokens das localizações. Verifique os logs.")
        exit(1)
    print(">>> SUCESSO: Tokens de todas as localizações foram processados.")


    print(f"\n=== PROCESSO CONCLUÍDO COM SUCESSO ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")