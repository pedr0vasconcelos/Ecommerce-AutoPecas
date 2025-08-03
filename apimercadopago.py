import mercadopago
from db_utils import get_user_db_connection


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
    payment = result["response"]
    return payment["init_point"]