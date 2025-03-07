import sqlite3 as sqlite
import datetime

def cria_tabela():
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dados_sensor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            luminosidade TEXT NOT NULL,
            umidade TEXT NOT NULL,
            temperatura TEXT NOT NULL,
            status TEXT NOT NULL,
            chuva TEXT NOT NULL,
            envio TEXT DEFAULT (DATETIME('now', 'localtime'))
        )
    ''')
    conn.commit()
    conn.close()

cria_tabela()

def inserir(lumin, umidade, temp, status, chuva):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dados_sensor (luminosidade, umidade, temperatura, status, chuva, envio) 
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
    ''', (lumin, umidade, temp, status, chuva))
    conn.commit()
    conn.close()


def listar():
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dados_sensor order by id desc')
    dados = cursor.fetchall()
    objetos = []
    for dado in dados:
        objetos.append(dado)
    conn.close()
    return objetos

def get_sensor(nome_sensor):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()
    #cursor.execute(f'SELECT {nome_sensor},datetime(envio, \'localtime\') FROM dados_sensor order by id asc')
    cursor.execute(f'SELECT {nome_sensor},envio FROM dados_sensor order by id asc')
    dados = cursor.fetchall()
    objetos = []
    for dado in dados:
        objetos.append(dado)
    conn.close()
    return objetos

def get_sensor24h(nome_sensor):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()

    agora = datetime.datetime.now()
    vinte_quatro_horas_atras = agora - datetime.timedelta(hours=24)
    vinte_quatro_horas_atras_str = vinte_quatro_horas_atras.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute(f'''
            SELECT {nome_sensor},envio FROM dados_sensor
            WHERE envio >= ?
        ''', (vinte_quatro_horas_atras_str,))

    dados = cursor.fetchall()
    objetos = []
    for dado in dados:
        objetos.append(dado)
    conn.close()
    return objetos


def login(email, senha):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM usuarios WHERE login='{email}' and senha= '{senha}'")

    dados = cursor.fetchall()#traz os dados

    conn.close()
    if len(dados) > 0:
        return True
    else:
        return False


