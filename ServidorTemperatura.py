from flask import *
import daofile
import grafico


app = Flask(__name__)

ip_local = '0.0.0.0'
porta_Local = 5001

temperatura = ''
umidade = ''

@app.route('/')
def abrir():
    return render_template('climanow.html', temperatura=temperatura, umidade=umidade)


@app.route('/temperatura', methods=['POST'])  # cadastrando uma rota
def recebe_dados():
    global temperatura, umidade

    data = request.json
    temperatura = data['temperatura']
    umidade = data['umidade']
    print(temperatura)
    print(umidade)
    return jsonify({'message': 'Dados salvos com sucesso'}), 200


if __name__ == '__main__':
    app.run(host=ip_local, port=porta_Local, debug=True)
