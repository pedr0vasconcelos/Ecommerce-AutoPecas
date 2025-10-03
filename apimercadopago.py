import mercadopago
from db_utils import get_user_db_connection

"""
IMPORTANTE: URLs do Localhost

O Mercado Pago não aceita URLs localhost (como http://127.0.0.1:5000) 
nas back_urls em ambiente de teste. Para desenvolvimento local, você tem 
algumas opções:

1. Usar ngrok para expor seu servidor local:
   - Instale ngrok: https://ngrok.com/
   - Execute: ngrok http 5000
   - Use a URL fornecida pelo ngrok nas back_urls

2. Usar URLs de teste (como httpbin.org) temporariamente

3. Em produção, use suas URLs reais do domínio

Para configurar adequadamente:
- Em desenvolvimento: Use ngrok ou URLs de teste
- Em produção: Use suas URLs reais (https://seudominio.com/...)
"""


def gerar_link_pagamento(itens):
    # Verificar se o token está configurado corretamente
    token = "TEST-3091909744318316-010415-4135841883ebe27a919b8c4f22a8fc75-48223634"
    if not token or not token.startswith("TEST-"):
        raise ValueError("Token do Mercado Pago não configurado corretamente")
    
    sdk = mercadopago.SDK(token)

    # Validar se há itens
    if not itens or len(itens) == 0:
        raise ValueError("Lista de itens está vazia")

    # Processa os itens (se necessário, para verificar ou modificar antes de enviar)
    itens_processados = []
    for item in itens:
        # Validar dados do item
        if not item.get("id"):
            raise ValueError(f"Item sem ID: {item}")
        if not item.get("title"):
            raise ValueError(f"Item sem título: {item}")
        if not item.get("quantity") or int(item.get("quantity")) <= 0:
            raise ValueError(f"Quantidade inválida para item {item.get('title')}: {item.get('quantity')}")
        if not item.get("unit_price") or float(item.get("unit_price")) <= 0:
            raise ValueError(f"Preço inválido para item {item.get('title')}: {item.get('unit_price')}")
            
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
            "success": "https://httpbin.org/get",  # Substitua por sua URL real em produção
            "failure": "https://httpbin.org/get",   # Substitua por sua URL real em produção
            "pending": "https://httpbin.org/get",   # Substitua por sua URL real em produção
        },
        # auto_return removido para funcionar com URLs de teste
        "external_reference": "LOJA_TERCOS_" + str(hash(str(itens_processados))),  # Referência única
    }

    result = sdk.preference().create(payment_data)
    
    # Verificar se a requisição foi bem-sucedida
    if result.get("status") != 201:
        raise Exception(f"Erro na API do Mercado Pago. Status: {result.get('status')}, Resposta: {result}")
    
    payment = result.get("response")
    if not payment:
        raise Exception(f"Resposta vazia da API do Mercado Pago: {result}")
    
    # Verificar se a chave init_point existe
    if "init_point" in payment:
        return payment["init_point"]
    else:
        # Retornar uma URL padrão ou levantar uma exceção mais informativa
        raise KeyError(f"'init_point' não encontrado na resposta do Mercado Pago. Resposta: {payment}")