from flask import jsonify
import requests
from config import estado_quarto, placas_registradas
import daofile
from datetime import datetime
from threading import Timer, Thread
import time


def _acionar(ip, acao, dispositivo):
    """Envia um comando e só considera o estado alterado após confirmação da placa."""
    if not ip:
        raise requests.exceptions.RequestException(
            f"IP da placa de {dispositivo} não encontrado."
        )

    resposta = requests.get(f'http://{ip}/{acao}', timeout=5)
    if resposta.status_code not in (200, 208):
        raise requests.exceptions.RequestException(
            f"Placa de {dispositivo} recusou /{acao} (status {resposta.status_code})."
        )


def _registrar_acoes(temperatura, umidade, acoes):
    """Persiste apenas decisões que realmente resultaram em comandos enviados."""
    if acoes:
        daofile.registrar_acao_agente(temperatura, umidade, estado_quarto, acoes)


def ajustar(temp_str, umid_str, dormir, aberta):
    print(f"Recebido - Temp: {temp_str}, Umid: {umid_str}, Dormir: {dormir}, Aberta(ESP): {aberta}")

    if None in (temp_str, umid_str, dormir, aberta):
        print("Erro: Requisição recebida sem os parâmetros corretos.")
        return jsonify({"erro": "Faltam parâmetros de temperatura, umidade, dormir ou aberta"}), 400

    try:
        temperatura = float(temp_str)
        umidade = float(umid_str)
        modo_dormir = int(dormir)
        janela_aberta = int(aberta)
        if modo_dormir not in (0, 1) or janela_aberta not in (0, 1):
            return jsonify({"erro": "Os estados dormir e aberta devem ser 0 ou 1"}), 400
        if not -20 <= temperatura <= 70:
            print(f"Erro: Temperatura recebida ({temperatura}°C) é irrealista.")
            return jsonify({"erro": "Temperatura irrealista"}), 400

        # Os estados enviados pela ESP são a fonte de verdade para a janela e o modo dormir.
        estado_quarto['dormir'] = modo_dormir
        estado_quarto['janela_aberta'] = janela_aberta

        daofile.inserir_th(umidade, temperatura)
        estado_quarto['temperatura_atual'] = float(temperatura)
        estado_quarto['umidade_atual'] = float(umidade)

        ip_janela = placas_registradas.get("janela")
        ip_ar = placas_registradas.get("esp8266ar")

        # ---------------------------------------------------------
        # REGRAS AUTOMÁTICAS DO QUARTO
        # ---------------------------------------------------------
        if estado_quarto['dormir'] == 1:
            hora_atual = datetime.now().hour

            # --- REGRA 1: ALCANCE DE CONFORTO (Abaixo de 26°C) ---
            # Primeiro desliga o ar e só depois abre a janela. Essa ordem impede
            # que os dois permaneçam ligados/abertos durante a transição.
            if temperatura < 26:
                acoes = []

                if estado_quarto['ar_ligado'] == 1:
                    _acionar(ip_ar, 'desligar', 'ar-condicionado')
                    estado_quarto['ar_ligado'] = 0
                    acoes.append("Ar Desligado")

                if estado_quarto['janela_aberta'] == 0:
                    _acionar(ip_janela, 'abrir', 'janela')
                    estado_quarto['janela_aberta'] = 1
                    acoes.append("Janela Aberta")

                if acoes:
                    print(f"Conforto Atingido ({temperatura}°C): {', '.join(acoes)} para manter a circulação.")
                    _registrar_acoes(temperatura, umidade, acoes)

            # --- REGRA 2: NOITES QUENTES (Acima do Limite de Conforto) ---
            # Temperatura subiu muito: isola o quarto fechando a janela e liga o resfriamento.
            elif temperatura > estado_quarto['temperatura_limite']:
                acoes = []

                if estado_quarto['janela_aberta'] == 1:
                    _acionar(ip_janela, 'fechar', 'janela')
                    estado_quarto['janela_aberta'] = 0
                    acoes.append("Janela Fechada")

                if estado_quarto['ar_ligado'] == 0:
                    _acionar(ip_ar, 'ligar', 'ar-condicionado')
                    estado_quarto['ar_ligado'] = 1
                    acoes.append("Ar Ligado")

                if acoes:
                    print(f"Quarto Quente ({temperatura}°C): {', '.join(acoes)} para resfriamento.")
                    _registrar_acoes(temperatura, umidade, acoes)

            # --- REGRA 3: INVARIANTE DE SEGURANÇA ---
            # A faixa entre 26°C e o limite é uma histerese: não liga nem desliga
            # o ar. Ainda assim, nunca permite ar ligado com a janela aberta.
            elif estado_quarto['ar_ligado'] == 1 and estado_quarto['janela_aberta'] == 1:
                _acionar(ip_janela, 'fechar', 'janela')
                estado_quarto['janela_aberta'] = 0
                print(
                    f"Correção de segurança ({temperatura}°C): "
                    "janela fechada porque o ar-condicionado está ligado."
                )
                _registrar_acoes(temperatura, umidade, ["Janela Fechada (segurança)"])

            # --- SKILL MADRUGADA (Otimização Energética entre 03h e 05h) ---
            if (0 <= hora_atual < 5) and estado_quarto['ar_ligado'] == 1 and temperatura <= 27:
                try:
                    acoes_madrugada = []
                    _acionar(ip_ar, 'desligar', 'ar-condicionado')
                    estado_quarto['ar_ligado'] = 0
                    acoes_madrugada.append("Ar Desligado (madrugada)")

                    if estado_quarto['janela_aberta'] == 0:
                        _acionar(ip_janela, 'abrir', 'janela')
                        estado_quarto['janela_aberta'] = 1
                        acoes_madrugada.append("Janela Aberta (madrugada)")

                    print("Skill Madrugada: Trocando Ar por janela para economizar energia.")
                    _registrar_acoes(temperatura, umidade, acoes_madrugada)
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
    """Roda em loop silencioso, mas só acessa a rede se o umidificador estiver ligado."""
    ip_vent = placas_registradas.get("esp32c3vent")
    if not ip_vent:
        print("[ÁGUA] Erro: IP da esp32c3vent não encontrado.")
        return

    print("[ÁGUA] Monitoramento do nível de água INICIADO (Standby).")

    while estado_quarto.get('monitor_agua', False):
        if estado_quarto.get('umidificador', 0) > 0:
            try:
                # Padronizado para /nivelagua (se na sua ESP for /nivel, mude aqui e no interface_bp.py)
                resposta = requests.get(f'http://{ip_vent}/nivel', timeout=5)

                if resposta.status_code == 200 and resposta.text.strip() == '1':
                    print("[ÁGUA] NÍVEL BAIXO DETECTADO! Desligando umidificador...")

                    # TRAVA DE SEGURANÇA: Limite de 4 tentativas para evitar loop infinito na rede
                    tentativas = 0
                    while estado_quarto['umidificador'] != 0 and tentativas < 4:
                        requests.get("http://127.0.0.1:5050/interf/ligarumidificador", timeout=5)
                        tentativas += 1
                        time.sleep(1.5)

                    if estado_quarto['umidificador'] != 0:
                        print("[ÁGUA] ALERTA: Falha ao tentar desligar o umidificador (ESP não respondeu).")

                    estado_quarto['monitor_agua'] = False
                    break

            except Exception as e:
                print(f"[ÁGUA] Falha ao ler sensor: {e}")

        # Retornado para 60 segundos. Protege a vida útil do aparelho se a água secar rápido.
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
