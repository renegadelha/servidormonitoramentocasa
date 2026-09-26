from flask import Blueprint, jsonify, render_template, request

import daofile


log_bp = Blueprint('log', __name__)


def obter_limite():
    """Lê o limite da consulta sem permitir que um valor inválido quebre a tela."""
    try:
        return max(1, min(int(request.args.get('limite', 100)), daofile.LIMITE_LOG_AGENTE))
    except (TypeError, ValueError):
        return 100


def serializar_evento(evento):
    horario, temperatura, umidade, dormir, janela, ar, ventilador, umidificador, acoes = evento
    return {
        'horario': horario,
        'temperatura': temperatura,
        'umidade': umidade,
        'dormir': bool(dormir),
        'janela_aberta': bool(janela),
        'ar_ligado': bool(ar),
        'ventilador': ventilador,
        'umidificador': umidificador,
        'acoes': acoes.split(',') if acoes else [],
    }


@log_bp.route('', methods=['GET'])
@log_bp.route('/', methods=['GET'])
def consultar_log_acoes_agente():
    limite = obter_limite()
    eventos = [serializar_evento(evento) for evento in daofile.listar_acoes_agente(limite)]
    return render_template('log_acoes_agente.html', eventos=eventos, limite=limite)


@log_bp.route('/api', methods=['GET'])
def consultar_log_acoes_agente_api():
    limite = obter_limite()
    eventos = [serializar_evento(evento) for evento in daofile.listar_acoes_agente(limite)]
    return jsonify({'limite': limite, 'eventos': eventos})


@log_bp.route('/dados-sensor', methods=['GET'])
def consultar_dados_sensor():
    dados_sensor = daofile.listar_ultimos_dados_sensor(200)
    return render_template('dados_sensor_recentes.html', dados_sensor=dados_sensor)
