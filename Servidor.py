from urllib import request

from flask import *
import daofile
import services
from controllers.admin_bp import admin_bp
from controllers.graficos_bp import graf_bp
from controllers.interface_bp import inter_bp
from controllers.log_bp import log_bp
from config import placas_registradas, estado_quarto

app = Flask(__name__)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(graf_bp, url_prefix='/graficos')
app.register_blueprint(inter_bp, url_prefix='/interf')
app.register_blueprint(log_bp, url_prefix='/log')

ip_local = '0.0.0.0'
porta_Local = 5050
print('oi')

@app.route('/placas', methods=['GET'])
def ver_status():
    if not placas_registradas:
        return jsonify({"mensagem": "Nenhuma placa registrada ainda."}), 200
    return jsonify(placas_registradas), 200


@app.route('/')
def home():
    temp = estado_quarto['temperatura_atual']
    umid = estado_quarto['umidade_atual']
    return render_template('homeinfo.html',temperatura_atual=temp, umidade_atual=umid)


@app.route('/meuip', methods=['GET'])
def registrar_ip():

    nome_placa = request.args.get('placa')
    ip_placa = request.args.get('ip')

    if not nome_placa or not ip_placa:
        return jsonify({"erro": "Parâmetros 'placa' e 'ip' são obrigatórios"}), 400
    #salvando dentro do dicionário
    placas_registradas[nome_placa] = ip_placa

    return jsonify({"status": "sucesso", "mensagem": "IP registrado corretamente"}), 200


@app.route('/ajustar', methods=['GET'])
def receber_dados():
    temp_str = request.args.get('temperatura')
    umid_str = request.args.get('umidade')
    dormir = request.args.get('dormir')
    aberta = request.args.get('aberta')
    luminosidade = request.args.get('luminosidade')
    
    return services.ajustar(temp_str, umid_str, dormir, aberta, luminosidade)


@app.route('/listar')
def listar():
    dados = daofile.listar()
    return render_template('index.html', dados_sensor=dados)


@app.route('/status')
def get_status():
    return services.pegar_status()


@app.route('/agendador')
def pagina_agendador():
    return render_template('agendador.html')

@app.route('/monitoramento', methods=['POST'])
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


@app.route('/ipesp')
def pegar_ipdaesp():
    ip = request.args.get('ip')
    print(ip)

if __name__ == '__main__':
    app.run(host=ip_local, port=porta_Local, debug=True)
