import asyncio
import json
import hmac
import hashlib
import base64
import time
import requests
import websockets

# --- CREDENCIAIS SINRIC PRO ---
APP_KEY = "e91db6ab-f56f-4251-a9fd-7b3c6a5f580e"
APP_SECRET = "9db9b342-23ea-487f-a559-7a1f708f879f-2f95e033-861c-4b5f-bc46-3871a5c17a3c"
JANELA_ID = "6a076c67f9b5f15fa7d5d63f"
DORMIR_ID = "6a0770ecf9b5f15fa7d5d940"
AR_CONDICIONADO_ID = "6a085dcdbaa50bf9bf34ec4e"

URI = "wss://ws.sinric.pro"

def gerar_assinatura(payload, secret):
    # A nuvem exige que a assinatura seja feita em cima da string exata do JSON (sem espaços)
    payload_str = json.dumps(payload, separators=(',', ':'))
    assinatura = hmac.new(secret.encode('utf-8'), payload_str.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(assinatura).decode('utf-8')

async def processar_mensagem(mensagem, websocket):
    dados = json.loads(mensagem)
    payload_recebido = dados.get("payload", {})
    action = payload_recebido.get("action")
    device_id = payload_recebido.get("deviceId")
    
    if action == "setPowerState":
        state = payload_recebido.get("value", {}).get("state")
        print(f"[COMANDO] Dispositivo: {device_id} | Ação: {state}")
        
        # 1. Disparar a ação no servidor Flask local
        try:
            if device_id == JANELA_ID:
                if state == "On":
                    requests.get("http://127.0.0.1:5050/interf/abrir")
                else:
                    requests.get("http://127.0.0.1:5050/interf/fechar")
            elif device_id == DORMIR_ID:
                requests.post("http://127.0.0.1:5050/interf/dormir")
            elif device_id == AR_CONDICIONADO_ID:
                if state == "On":
                    requests.get("http://127.0.0.1:5050/interf/ligarar")
                else:
                    requests.get("http://127.0.0.1:5050/interf/desligarar")
        except Exception as e:
            print(f"Erro ao comunicar com Flask: {e}")

        # 2. aqui  eu  preciso montar resposta p alexa
        payload_resposta = {
            "action": action,
            "clientId": payload_recebido.get("clientId", "alexa-skill"),
            "createdAt": int(time.time()),
            "deviceId": device_id,
            "messageId": payload_recebido.get("messageId"),
            "replyToken": payload_recebido.get("replyToken"),
            "success": True,
            "type": "response",
            "value": {"state": state}
        }
        
        # 3.  oia a criptografia sendo colocada  na versao 
        resposta_final = {
            "header": {"payloadVersion": 2, "signatureVersion": 1},
            "payload": payload_resposta,
            "signature": {"HMAC": gerar_assinatura(payload_resposta, APP_SECRET)}
        }
        
        await websocket.send(json.dumps(resposta_final))
        print("[RESPOSTA] Recibo de execução enviado para a nuvem.")

async def cliente_sinric():
    headers = {
        "appkey": APP_KEY,
        "deviceids": f"{JANELA_ID};{DORMIR_ID};{AR_CONDICIONADO_ID}",
        "restoredevicestates": "false"
    }
    
    while True:
        try:
            print("Conectando ao servidor da Sinric Pro...")
            async with websockets.connect(URI, additional_headers=headers) as websocket:
                print("Túnel WebSocket estabelecido! Ouvindo a Alexa de forma silenciosa e estável...")
                async for mensagem in websocket:
                    await processar_mensagem(mensagem, websocket)
        except Exception as e:
            print(f"Conexão perdida. Tentando novamente em 5s... Erro: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(cliente_sinric())
