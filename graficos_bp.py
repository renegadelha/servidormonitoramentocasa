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
    dados = daofile.filtrar_dados('temperatura')
    temperaturas = [float(item[0]) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas,'Temperatura')
    return render_template('view2.html', graph_html=html)

@graf_bp.route('/umidade')
def filtrar_grafico_umidade():
    dados = daofile.get_sensor24h('umidade')
    temperaturas = [float(item[0]) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas,'Temperatura')
    return render_template('view2.html', graph_html=html)


