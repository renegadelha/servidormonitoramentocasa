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

def inserir(lumin, umidade, temp, status, chuva):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dados_sensor (luminosidade, umidade, temperatura, status, chuva, envio) 
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
    ''', (lumin, umidade, temp, status, chuva))
    conn.commit()
    conn.close()

def inserir_th(umidade, temp):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dados_sensor (luminosidade, umidade, temperatura, status, chuva, envio) 
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
    ''', (0, umidade, temp, 0, 0))
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


def get_historico_agrupado(nome_sensor):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()

    query = f'''
        SELECT 
            AVG(CAST({nome_sensor} AS REAL)) as media_sensor,
            strftime('%Y-%m-%d %H:00:00', envio) as hora_agrupada
        FROM dados_sensor 
        GROUP BY hora_agrupada
        ORDER BY hora_agrupada ASC
    '''

    cursor.execute(query)
    dados = cursor.fetchall()
    conn.close()

    return dados


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


def filtrar_dados(sensor):
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()

    query = f"""
    SELECT {sensor},envio FROM dados_sensor
    WHERE CAST(temperatura AS REAL) < 28
    AND strftime('%H', envio) BETWEEN '00' AND '02'
    AND CAST(strftime('%M', envio) AS INTEGER) % 2 = 0
    AND CAST(strftime('%S', envio) AS INTEGER) % 2 = 0
    AND status == 'aberta'
    """

    cursor.execute(query)
    resultados = cursor.fetchall()
    conn.close()

    return resultados


def remover_dados_antigos(data_corte):
    """    Remove todos os registos anteriores à data especificada.     Formato da data_corte: 'YYYY-MM-DD'     """
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()


    query = '''
            DELETE \
            FROM dados_sensor
            WHERE envio < ? \
            '''

    cursor.execute(query, (f"{data_corte} 00:00:00",))
    linhas_apagadas = cursor.rowcount
    conn.commit()
    conn.close()

    return linhas_apagadas


def remover_temperaturas_absurdas(limite):
    """    aqui removo todos os registos onde a temperatura seja superior ao limite informado   """
    conn = sqlite.connect('db2.sqlite')
    cursor = conn.cursor()

    query = '''
            DELETE \
            FROM dados_sensor
            WHERE CAST(temperatura AS REAL) > ? \
            '''

    cursor.execute(query, (limite,))
    linhas_apagadas = cursor.rowcount
    conn.commit()
    conn.close()

    return linhas_apagadas
