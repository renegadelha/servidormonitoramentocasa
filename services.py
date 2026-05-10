from flask import jsonify, request
import requests
from config import TEMPERATURA_LIMITE_FECHAR, estado_quarto, placas_registradas
import daofile


def ajustar(temp_str, umid_str, dormir, aberta):
    estado_quarto['dormir'] = int(dormir)
    estado_quarto['janela_fechada'] = int(aberta)

    print(temp_str, umid_str, dormir, aberta)

    if temp_str is None or umid_str is None:
        print("Erro: Requisição recebida sem os parâmetros corretos.")
        return jsonify({"erro": "Faltam parâmetros de temperatura ou umidade"}), 400

    try:
        temperatura = float(temp_str)
        umidade = float(umid_str)
        daofile.inserir_th(umidade, temperatura)

        if estado_quarto['modo_dormir'] and temperatura > 28.0 and not estado_quarto['ar_ligado']:
            try:
                if not estado_quarto['janela_fechada']:
                    requests.get(f'http://{placas_registradas.get('esp32')}/fechar', timeout=13)
                    estado_quarto['janela_fechada'] = 1

                if not estado_quarto['ar_ligado']:
                    requests.get(f'http://{placas_registradas.get('esp8266ar')}/ligar', timeout=3)
                    estado_quarto['ar_ligado'] = 1

            except requests.exceptions.RequestException as e:
                print(f"Erro ao comunicar com as placas: {e}")
                return jsonify({"status": "erro", "mensagem": "Erro ao comunicar com as placas!"}), 400
        return jsonify({"status": "sucesso", "mensagem": "Dados gravados com sucesso!"}), 200

    except ValueError:

        return jsonify({"erro": "Os valores devem ser numéricos (float)"}), 400


def ajuster_temp_limite(tempo):
    global TEMPERATURA_LIMITE_FECHAR
    try:
        TEMPERATURA_LIMITE_FECHAR = float(tempo)
        return 'ok', 200
    except ValueError:
        print('nao recebi')
        return 'erro', 400


