from flask import *
import requests
import services
from config import estado_quarto, placas_registradas

inter_bp = Blueprint('interf', __name__)


@inter_bp.route('/dormir', methods=['POST','GET'])
def alternar_modo_dormir():
    estado_atual = estado_quarto['dormir']
    estado_pretendido = 1 if estado_atual == 0 else 0

    estado_texto = "entrando" if estado_pretendido == 1 else "saindo"
    ip_esp32 = placas_registradas.get('janela')

    if not ip_esp32:
        return jsonify({"erro": "IP da ESP32 não encontrado no registo."}), 404

    url = f"http://{ip_esp32}/dormir"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            estado_quarto['dormir'] = estado_pretendido

            return jsonify({
                "mensagem": f"ESP32 informada: {estado_texto} em modo dormir.",
                "modo_dormir": True if estado_pretendido == 1 else False
            }), 200
        else:
            return jsonify({"erro": f"Placa respondeu com erro: {response.status_code}"}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"erro": f"Falha de comunicação com a placa: {str(e)}"}), 503


@inter_bp.route('/ajustar_limite', methods=['GET'])
def ajuster_temp_limit():
    temp = request.args.get('temp')
    return services.ajuster_temp_limite(temp)

@inter_bp.route('/status_alexa')
def status_alexa():
    # Retorna sempre "on" em texto puro.
    # Isso é só para a Alexa ficar feliz durante a descoberta e não dar erro.
    return "on", 200

@inter_bp.route('/abrir')
def abrir_janela_endpoint():
    ip_esp32 = placas_registradas.get('janela')
    if not ip_esp32:
        return jsonify({"erro": "IP da ESP32 não encontrado"}), 404

    url = f"http://{ip_esp32}/abrir"
    try:
        response = requests.get(url, timeout=15)

        if response.status_code == 200:

            estado_quarto['janela_aberta'] = 1
            return jsonify({
                "status": "sucesso",
                "mensagem": "Janela aberta com sucesso",
                "estado_janela": "aberta"
            }), 200

        elif response.status_code == 208:

            estado_quarto['janela_aberta'] = 1
            return jsonify({
                "status": "aviso",
                "mensagem": "A janela já se encontrava aberta",
                "estado_janela": "aberta"
            }), 200

        else:
            return jsonify({"erro": f"Placa retornou status inesperado: {response.status_code}"}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"erro": f"Falha de comunicação com a ESP32: {str(e)}"}), 503


@inter_bp.route('/fechar')
def fechar_janela_endpoint():
    ip_esp32 = placas_registradas.get('janela')
    if not ip_esp32:
        return jsonify({"erro": "IP da ESP32 não encontrado"}), 404

    url = f"http://{ip_esp32}/fechar"
    try:
        response = requests.get(url, timeout=15)

        if response.status_code == 200:

            estado_quarto['janela_aberta'] = 0
            estado_quarto['dormir'] = 0

            return jsonify({
                "status": "sucesso",
                "mensagem": "Janela fechada com sucesso",
                "estado_janela": "fechada"
            }), 200

        elif response.status_code == 208:

            estado_quarto['janela_aberta'] = 0
            return jsonify({
                "status": "aviso",
                "mensagem": "A janela já se encontrava fechada",
                "estado_janela": "fechada"
            }), 200

        else:
            return jsonify({"erro": f"Placa retornou status inesperado: {response.status_code}"}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"erro": f"Falha de comunicação com a ESP32: {str(e)}"}), 503