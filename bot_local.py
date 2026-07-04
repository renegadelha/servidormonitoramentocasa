import telebot
import requests


TOKEN = '8687595101:AAFCnyw9zTMOwLmJhRwmgYhahFXFbulMk-I'
MEU_CHAT_ID = 8357123466
URL_SERVIDOR_LOCAL = 'http://192.168.0.117/'

bot = telebot.TeleBot(TOKEN)


def enviar_para_esp32(endpoint, params=None):

    try:

        resposta = requests.get(URL_SERVIDOR_LOCAL + endpoint, params=params, timeout=12)

        if resposta.status_code == 200:
            return resposta.text
        else:
            return f"Erro na ESP32 (Status {resposta.status_code}): {resposta.text}"

    except requests.exceptions.RequestException as e:
        return f"Falha de conexão com a ESP32. Ela está ligada na mesma rede?\nDetalhe: {e}"


@bot.message_handler(commands=['abrir', 'fechar', 'tafechada', 'dormir', 'status'])
def comandos_simples(message):
    if message.chat.id != MEU_CHAT_ID:
        return

    comando = message.text.split()[0]
    print(comando)
    bot.reply_to(message, f"Executando {comando} na ESP32...")

    resposta_esp = enviar_para_esp32(comando)
    bot.reply_to(message, f"**Resposta:**\n{resposta_esp}", parse_mode="Markdown")
print("Bot rodando na Rasp...")
bot.infinity_polling()