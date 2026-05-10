from flask import *
import daofile
import grafico
import services
from graficos_bp import graf_bp
from interface_bp import inter_bp
from config import TEMPERATURA_LIMITE_FECHAR, estado_quarto, placas_registradas

app = Flask(__name__)

app.register_blueprint(graf_bp, url_prefix='/graficos')
app.register_blueprint(inter_bp, url_prefix='/interf')

ip_local = '0.0.0.0'
porta_Local = 5050


@app.route('/placas', methods=['GET'])
def ver_status():
    if not placas_registradas:
        return jsonify({"mensagem": "Nenhuma placa registrada ainda."}), 200
    return jsonify(placas_registradas), 200


@app.route('/')
def home():
    return render_template('homeinfo.html')


@app.route('/meuip', methods=['GET'])
def registrar_ip():

    nome_placa = request.args.get('placa')
    ip_placa = request.args.get('ip')

    if not nome_placa or not ip_placa:
        return jsonify({"erro": "Parâmetros 'placa' e 'ip' são obrigatórios"}), 400

    placas_registradas[nome_placa] = ip_placa

    return jsonify({"status": "sucesso", "mensagem": "IP registrado corretamente"}), 200


@app.route('/ajustar', methods=['GET'])
def receber_dados():
    temp_str = request.args.get('temperatura')
    umid_str = request.args.get('umidade')
    dormir = request.args.get('dormir')
    aberta = request.args.get('aberta')

    return services.ajustar(temp_str, umid_str, dormir, aberta)


@app.route('/listar')
def listar():
    dados = daofile.listar()
    return render_template('index.html', dados_sensor=dados)


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


if __name__ == '__main__':
    app.run(host=ip_local, port=porta_Local, debug=True)
