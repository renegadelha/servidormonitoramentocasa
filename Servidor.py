from flask import *
import daofile
import grafico


app = Flask(__name__)

ip_local = '0.0.0.0'
porta_Local = 5001

@app.route('/')
def abrir():
    return render_template('homeinfo.html')

@app.route('/listar')
def listar():
    dados = daofile.listar()
    return render_template('index.html', dados_sensor=dados)


@app.route('/grafico')
def mostrar_grafico():
    dados = daofile.get_sensor24h('temperatura')
    temperaturas = [float(item[0]) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas,'Temperatura')
    return render_template('view.html', graph_html=html)



@app.route('/graficotemp')
def filtrar_grafico_temp():
    dados = daofile.filtrar_dados('temperatura')
    temperaturas = [float(item[0]) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas,'Temperatura')
    return render_template('view2.html', graph_html=html)

@app.route('/graficoumidade')
def filtrar_grafico_umidade():
    dados = daofile.filtrar_dados('umidade')
    temperaturas = [float(item[0]) for item in dados]
    horas = [item[1] for item in dados]

    html = grafico.gerar_grafico2(temperaturas, horas,'Temperatura')
    return render_template('view2.html', graph_html=html)

@app.route('/monitoramento', methods=['POST'])  # cadastrando uma rota
def recebe_dados():
    data = request.json
    temp = data['temperatura']
    umidade = data['umidade']
    lumin = data['luminosidade']
    status_janela = 'aberta' if int(data['statusjanela']) == 1 else 'fechada'
    chuva = int(data['chuva'])

    chuva = 100 - (chuva / 4095) * 100
    chuva = round(chuva, 1)
    daofile.inserir(lumin,umidade,temp, status_janela, chuva)

    return jsonify({'message': 'Dados salvos com sucesso'}), 200

@app.route('/fechar')
def fechar_janela():
    print('recebi o fechar janela')
    return 'ok',200


@app.route('/ajustar', methods=['GET'])
def receber_dados():
    temp_str = request.args.get('temperatura')
    umid_str = request.args.get('umidade')
    chuva = request.args.get('chuva')
    print(temp_str, umid_str, chuva)

    if temp_str is None or umid_str is None:
        print("Erro: Requisição recebida sem os parâmetros corretos.")
        return jsonify({"erro": "Faltam parâmetros de temperatura ou umidade"}), 400

    try:
        temperatura = float(temp_str)
        umidade = float(umid_str)
        daofile.inserir_th(umidade, temperatura)
        return jsonify({"status": "sucesso", "mensagem": "Dados gravados com sucesso!"}), 200

    except ValueError:

        return jsonify({"erro": "Os valores devem ser numéricos (float)"}), 400

if __name__ == '__main__':
    app.run(host=ip_local, port=porta_Local, debug=True)
