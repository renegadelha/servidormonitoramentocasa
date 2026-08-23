from flask import jsonify
import requests
from config import estado_quarto, placas_registradas
import daofile
from datetime import datetime
from threading import Timer, Thread
import time


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
        estado_quarto['temperatura_atual'] = float(temperatura)
        estado_quarto['umidade_atual'] = float(umidade)

        ip_janela = placas_registradas.get("janela")
        ip_ar = placas_registradas.get("esp8266ar")
        ip_vent = placas_registradas.get("esp32c3vent")

        # ---------------------------------------------------------
        # REGRAS AUTOMÁTICAS DO QUARTO
        # ---------------------------------------------------------
        if estado_quarto['dormir'] == 1:
            hora_atual = datetime.now().hour

            # --- REGRA 1: ALCANCE DE CONFORTO (Abaixo de 26°C) ---
            # O quarto já resfriou o suficiente. Desliga o ar e abre a janela
            # para evitar o efeito "estufa" e manter a circulação com o ar da rua.
            if temperatura < 26:
                acoes = []

                if estado_quarto['janela_aberta'] == 0:
                    requests.get(f'http://{ip_janela}/abrir', timeout=5)
                    estado_quarto['janela_aberta'] = 1
                    acoes.append("Janela Aberta")

                if estado_quarto['ar_ligado'] == 1:
                    requests.get(f'http://{ip_ar}/desligar', timeout=5)
                    estado_quarto['ar_ligado'] = 0
                    acoes.append("Ar Desligado")

                if acoes:
                    print(f"Conforto Atingido ({temperatura}°C): {', '.join(acoes)} para manter a circulação.")

            # --- REGRA 2: NOITES QUENTES (Acima do Limite de Conforto) ---
            # Temperatura subiu muito: isola o quarto fechando a janela e liga o resfriamento.
            elif temperatura > estado_quarto['temperatura_limite']:
                acoes = []

                if estado_quarto['janela_aberta'] == 1:
                    requests.get(f'http://{ip_janela}/fechar', timeout=5)
                    estado_quarto['janela_aberta'] = 0
                    acoes.append("Janela Fechada")

                if estado_quarto['ar_ligado'] == 0:
                    requests.get(f'http://{ip_ar}/ligar', timeout=5)
                    estado_quarto['ar_ligado'] = 1
                    acoes.append("Ar Ligado")

                if acoes:
                    print(f"Quarto Quente ({temperatura}°C): {', '.join(acoes)} para resfriamento.")

            # --- SKILL MADRUGADA (Otimização Energética entre 03h e 05h) ---
            if (2 <= hora_atual < 5) and estado_quarto['ar_ligado'] == 1 and temperatura <= 27:
                try:
                    requests.get(f'http://{ip_ar}/desligar', timeout=5)
                    estado_quarto['ar_ligado'] = 0

                    if estado_quarto['janela_aberta'] == 0:
                        requests.get(f'http://{ip_janela}/abrir', timeout=5)
                        estado_quarto['janela_aberta'] = 1

                    print("Skill Madrugada: Trocando Ar por janela para economizar energia.")
                except Exception as e:
                    print(f"Erro na Skill Madrugada: {e}")

        return jsonify({"status": "sucesso", "mensagem": f"Regras aplicadas para {temperatura}°C"}), 200

    except ValueError:
        return jsonify({"erro": "Os valores devem ser numéricos (float)"}), 400
    except requests.exceptions.RequestException as e:
        print(f"Erro de comunicação: {e}")
        return jsonify({"status": "erro", "mensagem": "Falha ao comunicar com os dispositivos"}), 503

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


# Dicionário global para guardar os agendamentos ativos
timers_ativos = {}


def executar_desligamento(dispositivo):
    """Função que roda em segundo plano quando o cronômetro zera"""
    print(f"[AGENDADOR] O tempo acabou! Desligando {dispositivo}...")

    try:
        if dispositivo == "ar":
            requests.get("http://127.0.0.1:5050/interf/desligarar", timeout=5)

        elif dispositivo == "ventilador":
            while estado_quarto['ventilador'] != 0:
                requests.get("http://127.0.0.1:5050/interf/ligarventilador", timeout=5)
                time.sleep(1.5)

        elif dispositivo == "umidificador":
            while estado_quarto['umidificador'] != 0:
                requests.get("http://127.0.0.1:5050/interf/ligarumidificador", timeout=5)
                time.sleep(1.5)

    except Exception as e:
        print(f"[AGENDADOR] Erro ao executar desligamento do {dispositivo}: {e}")


def criar_agendamento(dispositivo, horas, minutos):
    """Regra de negócio para criar ou cancelar o timer"""
    tempo_segundos = (horas * 3600) + (minutos * 60)

    # Cancela o timer se o tempo for 0
    if tempo_segundos <= 0:
        if dispositivo in timers_ativos:
            timers_ativos[dispositivo].cancel()
            del timers_ativos[dispositivo]
        return {"status": "sucesso", "mensagem": f"Agendamento do {dispositivo} cancelado."}

    # Sobrescreve timer existente
    if dispositivo in timers_ativos:
        timers_ativos[dispositivo].cancel()

    t = Timer(tempo_segundos, executar_desligamento, args=[dispositivo])
    t.start()

    timers_ativos[dispositivo] = t
    return {"status": "sucesso", "mensagem": f"{dispositivo.capitalize()} será desligado em {horas}h e {minutos}m."}


def vigiar_nivel_agua():
    """Roda em loop silencioso a cada 60s, mas só acessa a rede se o umidificador estiver ligado."""
    ip_vent = placas_registradas.get("esp32c3vent")
    if not ip_vent:
        print("[ÁGUA] Erro: IP da esp32c3vent não encontrado.")
        return

    print("[ÁGUA] Monitoramento do nível de água INICIADO (Standby).")

    # O loop principal continua rodando enquanto a chave do painel for True
    while estado_quarto.get('monitor_agua', False):

        # A MÁGICA AQUI: Só faz a requisição HTTP para a placa se o aparelho estiver ligado (nível 1, 2 ou 3)
        if estado_quarto.get('umidificador', 0) > 0:
            try:
                resposta = requests.get(f'http://{ip_vent}/nivel', timeout=5)

                # Se a placa responder 1 (vazio)
                if resposta.status_code == 200 and resposta.text.strip() == '1':
                    print("[ÁGUA] NÍVEL BAIXO DETECTADO! Desligando umidificador...")

                    # Usa a mesma lógica cíclica para garantir que ele volte para o 0
                    while estado_quarto['umidificador'] != 0:
                        requests.get("http://127.0.0.1:5050/interf/ligarumidificador", timeout=5)
                        time.sleep(1.5)

                    # Desativa o botão do painel de monitoramento para o usuário saber que a proteção atuou
                    estado_quarto['monitor_agua'] = False
                    break

            except Exception as e:
                print(f"[ÁGUA] Falha ao ler sensor: {e}")

        # Quer tenha feito a checagem na placa ou apenas pulado o IF, aguarda 60s para o próximo ciclo
        time.sleep(200)


def alternar_monitor_agua(ativar):
    """Ativa ou desativa a Thread dependendo da ordem do painel web"""
    estado_atual = estado_quarto.get('monitor_agua', False)
    novo_estado = ativar == 'true'

    if novo_estado and not estado_atual:
        estado_quarto['monitor_agua'] = True
        t = Thread(target=vigiar_nivel_agua)
        t.daemon = True  # Garante que a thread feche se o Gunicorn for reiniciado
        t.start()
        return {"status": "sucesso", "mensagem": "Monitoramento ATIVADO.", "monitor_agua": True}

    elif not novo_estado and estado_atual:
        estado_quarto['monitor_agua'] = False
        return {"status": "sucesso", "mensagem": "Monitoramento DESATIVADO.", "monitor_agua": False}

    return {"status": "aviso", "mensagem": "O estado já é o solicitado.", "monitor_agua": novo_estado}