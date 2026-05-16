from flask import jsonify
import requests
from config import estado_quarto, placas_registradas
import daofile

def ajustar(temp_str, umid_str, dormir, aberta):
    estado_quarto['dormir'] = int(dormir)
    estado_quarto['janela_aberta'] = int(aberta)

    print(f"Recebido - Temp: {temp_str}, Umid: {umid_str}, Dormir: {dormir}, Aberta(ESP): {aberta}")

    if temp_str is None or umid_str is None:
        print("Erro: Requisição recebida sem os parâmetros corretos.")
        return jsonify({"erro": "Faltam parâmetros de temperatura ou umidade"}), 400

    try:
        temperatura = float(temp_str)
        umidade = float(umid_str)
        daofile.inserir_th(umidade, temperatura)

        if estado_quarto['dormir'] == 1 and temperatura > estado_quarto['temperatura_limite'] and estado_quarto['ar_ligado'] == 0:
            try:

                if estado_quarto['janela_aberta'] == 1:
                    requests.get(f'http://{placas_registradas.get("janela")}/fechar', timeout=13)

                    estado_quarto['janela_aberta'] = 0

                if estado_quarto['ar_ligado'] == 0:
                    requests.get(f'http://{placas_registradas.get("esp8266ar")}/ligar', timeout=3)
                    estado_quarto['ar_ligado'] = 1

            except requests.exceptions.RequestException as e:
                print(f"Erro ao comunicar com as placas: {e}")
                return jsonify({"status": "erro", "mensagem": "Erro ao comunicar com as placas!"}), 503

        if estado_quarto['dormir'] == 1 and temperatura < 26 and estado_quarto['janela_aberta'] == 1:
            try:
                requests.get(f'http://{placas_registradas.get("janela")}/fechar', timeout=13)
                estado_quarto['janela_aberta'] = 0
            except requests.exceptions.RequestException as e:
                return jsonify({'status':'erro', 'mensagem':'Ao tentar comunicar com a janela, houve erro de conexão'})


        return jsonify({"status": "sucesso", "mensagem": "Dados gravados com sucesso!"}), 200

    except ValueError:
        return jsonify({"erro": "Os valores devem ser numéricos (float)"}), 400


def ajuster_temp_limite(tempo):

    try:
        estado_quarto['temperatura_limite'] = float(tempo)
        return 'ok', 200
    except ValueError:
        print('nao recebi limite valido')
        return 'erro', 400


def pegar_status():
    try:
        ip_esp32 = placas_registradas.get('janela')
        if not ip_esp32:
            return "Erro: IP da ESP32 (janela) não encontrado."

        url = f"http://{ip_esp32}/status"
        resposta = requests.get(url, timeout=5)

        if resposta.status_code == 200:
            return resposta.text
        else:
            return f"Erro na ESP32 (Status {resposta.status_code}): {resposta.text}"

    except requests.exceptions.RequestException as e:
        return f"Falha de conexão com a ESP32. Ela está ligada na mesma rede?\nDetalhe: {e}"