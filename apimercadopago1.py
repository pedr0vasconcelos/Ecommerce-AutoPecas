import mercadopago
from db_utils import get_user_db_connection
import json # Importe para debug

def gerar_link_pagamento(itens):
    sdk = mercadopago.SDK("TEST-3091909744318316-010415-4135841883ebe27a919b8c4f22a8fc75-48223634")

    # Processa os itens (se necessário, para verificar ou modificar antes de enviar)
    itens_processados = []
    for item in itens:
        item_processado = {
            "id": str(item.get("id")),
            "title": item.get("title", "Produto sem nome"),  # Nome do produto
            "quantity": int(item.get("quantity", 1)),  # Quantidade
            "currency_id": "BRL",  # Moeda
            "unit_price": float(item.get("unit_price", 0.0)),  # Preço unitário
        }
        itens_processados.append(item_processado)

    payment_data = {
        "items": itens_processados,  # Passa a lista processada
        "back_urls": {
            "success": "http://127.0.0.1:5000/compracerta",
            "failure": "http://127.0.0.1:5000/compraerrada",
            "pending": "http://127.0.0.1:5000/compraerrada",
        },
        "auto_return": "approved",
    }

    result = sdk.preference().create(payment_data)
    
    # 1. Verifica o status HTTP da resposta
    if 'status' in result and result['status'] in [200, 201] and 'response' in result:
        payment = result["response"]
        # 2. Verifica se a resposta contém o 'init_point'
        if "init_point" in payment:
            return payment["init_point"]
        else:
            # Caso raro: Sucesso sem o campo esperado (pode ser um erro de documentação/SDK)
            print("ERRO MP: Resposta de sucesso não contém 'init_point'. Resposta completa:")
            print(json.dumps(result, indent=4))
            return None # Retorna None em caso de falha de estrutura

    # Caso a chamada tenha falhado (status diferente de 200/201)
    else:
        print("ERRO MP: Falha ao criar a preferência de pagamento. Status/Erro:")
        print(json.dumps(result, indent=4))
        return None # Retorna None em caso de falha