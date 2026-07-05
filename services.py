from flask import jsonify
import requests
from config import estado_quarto, placas_registradas
import daofile
from datetime import datetime

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
        if temperatura > 70:
            print(f"Erro: Temperatura recebida ({temperatura}°C) é irrealista.")
            return jsonify({"erro": "Temperatura irrealista"}), 400
        
        daofile.inserir_th(umidade, temperatura)

        # Só executa as regras de automação se o modo dormir estiver ativado
        if estado_quarto['dormir'] == 1:
            hora_atual = datetime.now().hour
            ip_janela = placas_registradas.get("janela")
            ip_ar = placas_registradas.get("esp8266ar")
            
            # --- REGRA 1: NOITES FRIAS (Abaixo de 26°C) ---
            if temperatura < 26:
                if estado_quarto['janela_aberta'] == 1:
                    requests.get(f'http://{ip_janela}/fechar', timeout=5)
                    # A ESP32 desativa o modo dormir ao fechar, então reativamos
                    requests.get(f'http://{ip_janela}/dormir', timeout=5)
                    estado_quarto['janela_aberta'] = 0
                    estado_quarto['dormir'] = 1
                if estado_quarto['ar_ligado'] == 1:
                    requests.get(f'http://{ip_ar}/desligar', timeout=5)
                    estado_quarto['ar_ligado'] = 0
                print(f"Noite Fria ({temperatura}°C): Fechando tudo.")

            # --- REGRA 2: NOITES QUENTES mas liguei AR (Abaixo de 26°C) ---
            if temperatura < 26 and estado_quarto['ar_ligado'] == 1:
                if estado_quarto['janela_aberta'] == 0:
                    requests.get(f'http://{ip_janela}/abrir', timeout=5)
                    estado_quarto['janela_aberta'] = 1
                if estado_quarto['ar_ligado'] == 1:
                    requests.get(f'http://{ip_ar}/desligar', timeout=5)
                    estado_quarto['ar_ligado'] = 0
                print(f"Noite Fria ({temperatura}°C): Fechando tudo.")


            # --- REGRA 3: NOITES QUENTES (Acima de 2limite)
            elif temperatura > estado_quarto['temperatura_limite']:
                # Se estiver quente, fecha a janela para o ar condicionado ser eficiente
                if estado_quarto['janela_aberta'] == 1:
                    requests.get(f'http://{ip_janela}/fechar', timeout=5)
                    # A ESP32 desativa o modo dormir ao fechar, então reativamos
                    requests.get(f'http://{ip_janela}/dormir', timeout=5)
                    estado_quarto['janela_aberta'] = 0
                    estado_quarto['dormir'] = 1
                
                # Liga o ar condicionado se estiver desligado
                if estado_quarto['ar_ligado'] == 0:
                    requests.get(f'http://{ip_ar}/ligar', timeout=5)
                    estado_quarto['ar_ligado'] = 1
                print(f"Noite Quente ({temperatura}°C): Ar condicionado ativado.")

            # --- SKILL MADRUGADA (Otimização Energética entre 03h e 05h) ---
            # Se o ar estiver ligado mas a temperatura externa/interna já está baixando
            if (3 <= hora_atual < 5) and estado_quarto['ar_ligado'] == 1 and temperatura <= 27:
                try:
                    requests.get(f'http://{ip_ar}/desligar', timeout=5)
                    estado_quarto['ar_ligado'] = 0
                    requests.get(f'http://{ip_janela}/abrir', timeout=5)
                    estado_quarto['janela_aberta'] = 1
                    print("Skill Madrugada: Trocando Ar por janela para economizar.")
                except Exception as e:
                    print(f"Erro na Skill Madrugada: {e}")

            return jsonify({"status": "sucesso", "mensagem": f"Regras aplicadas para {temperatura}°C"}), 200

        return jsonify({"status": "sucesso", "mensagem": "Dados gravados (Modo Acordado)"}), 200

    except ValueError:
        return jsonify({"erro": "Os valores devem ser numéricos (float)"}), 400
    except requests.exceptions.RequestException as e:
        print(f"Erro de comunicação: {e}")
        return jsonify({"status": "erro", "mensagem": "Falha ao comunicar com os dispositivos"}), 503

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
            return resposta.text + '\n\n' + str(estado_quarto)
        else:
            return f"Erro na ESP32 (Status {resposta.status_code}): {resposta.text}"

    except requests.exceptions.RequestException as e:
        return f"Falha de conexão com a ESP32. Ela está ligada na mesma rede?\nDetalhe: {e}"