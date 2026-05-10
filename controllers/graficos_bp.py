from flask import *
import daofile
import grafico
graf_bp = Blueprint('graficos', __name__)


@graf_bp.route('/')
def mostrar_grafico():
    dados = daofile.get_sensor24h('temperatura')
    temperaturas = [float(item[0]) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas,'Temperatura')
    return render_template('view.html', graph_html=html)


@graf_bp.route('/temp')
def filtrar_grafico_temp():
    dados = daofile.get_historico_agrupado('temperatura')

    temperaturas = [round(float(item[0]), 1) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas, 'Histórico Completo de Temperatura (Média Horária)')

    return render_template('view2.html', graph_html=html)

@graf_bp.route('/umidade')
def filtrar_grafico_umidade():
    dados = daofile.get_historico_agrupado('umidade')

    umidades = [round(float(item[0]), 1) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(umidades, horas, 'Histórico Completo de Umidade (Média Horária)')

    return render_template('view2.html', graph_html=html)


