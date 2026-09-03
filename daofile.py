import sqlite3 as sqlite
import datetime


# Este banco é separado da telemetria bruta: só recebe eventos quando o agente
# automático toma uma ação. O limite mantém o arquivo pequeno mesmo após anos.
ARQUIVO_LOG_AGENTE = 'log_agente.sqlite'
RETENCAO_LOG_AGENTE_DIAS = 90
LIMITE_LOG_AGENTE = 3000


def registrar_acao_agente(temperatura, umidade, estado, acoes):
    """Registra uma decisão já executada pelo agente sem interromper a automação."""
    try:
        with sqlite.connect(ARQUIVO_LOG_AGENTE) as conn:
            # auto_vacuum só tem efeito ao criar o banco; reduz espaço livre após a retenção.
            conn.execute('PRAGMA auto_vacuum = INCREMENTAL')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS acoes_agente (
                    id INTEGER PRIMARY KEY,
                    horario TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    temperatura REAL NOT NULL,
                    umidade REAL NOT NULL,
                    dormir INTEGER NOT NULL,
                    janela_aberta INTEGER NOT NULL,
                    ar_ligado INTEGER NOT NULL,
                    ventilador INTEGER NOT NULL,
                    umidificador INTEGER NOT NULL,
                    acoes TEXT NOT NULL
                )
            ''')
            conn.execute('''
                INSERT INTO acoes_agente
                    (temperatura, umidade, dormir, janela_aberta, ar_ligado,
                     ventilador, umidificador, acoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                temperatura,
                umidade,
                estado['dormir'],
                estado['janela_aberta'],
                estado['ar_ligado'],
                estado.get('ventilador', 0),
                estado.get('umidificador', 0),
                ','.join(acoes),
            ))

            conn.execute('''
                DELETE FROM acoes_agente
                WHERE horario < datetime('now', 'localtime', ?)
            ''', (f'-{RETENCAO_LOG_AGENTE_DIAS} days',))
            conn.execute('''
                DELETE FROM acoes_agente
                WHERE id NOT IN (
                    SELECT id FROM acoes_agente ORDER BY id DESC LIMIT ?
                )
            ''', (LIMITE_LOG_AGENTE,))
            conn.execute('PRAGMA incremental_vacuum(1)')
    except sqlite.Error as erro:
        # O log é observabilidade; uma falha nele não pode impedir uma ação física.
        print(f"[LOG AGENTE] Não foi possível gravar o evento: {erro}")


def listar_acoes_agente(limite=100):
    """Retorna os eventos mais recentes para uma futura tela ou API de auditoria."""
    limite = max(1, min(int(limite), LIMITE_LOG_AGENTE))
    try:
        with sqlite.connect(ARQUIVO_LOG_AGENTE) as conn:
            return conn.execute('''
                SELECT horario, temperatura, umidade, dormir, janela_aberta,
                       ar_ligado, ventilador, umidificador, acoes
                FROM acoes_agente
                ORDER BY id DESC
                LIMIT ?
            ''', (limite,)).fetchall()
    except sqlite.Error:
        return []

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
