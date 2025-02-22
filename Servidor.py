from flask import *
import daofile
import grafico
import grafico as gr

app = Flask(__name__)

ip_local = '0.0.0.0'
porta_Local = 5050


@app.route('/')
def abrir():
    return render_template('abrir.html')

@app.route('/listar')
def listar():
    dados = daofile.listar()
    return render_template('index.html', dados_sensor=dados)


@app.route('/grafico')
def mostrar_grafico():
    dados = daofile.get_sensor('temperatura')
    temperaturas = [float(item[0]) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas,'Temperatura')
    return render_template('view.html', graph_html=html)

@app.route('/monitoramento', methods=['POST'])  # cadastrando uma rota
def recebe_dados():
    data = request.json
    temp = data['temperatura']
    umidade = data['umidade']
    lumin = data['luminosidade']

    daofile.inserir(lumin,umidade,temp)

    return jsonify({'message': 'Dados salvos com sucesso'}), 200


if __name__ == '__main__':
    app.run(host=ip_local, port=porta_Local, debug=True)
