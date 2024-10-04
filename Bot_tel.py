import requests
import mysql.connector
from mysql.connector import Error
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
#
# Configura les teves API keys
API_KEY_OPENWEATHER = '9e861594dcc5aae42068292ef836f318'
API_KEY_TELEGRAM = '7750424681:AAHBQ8BGfHf6-pv2r6dWY9Gos0OzGnYLXcc'


# Funció per connectar-se a MariaDB
def crear_connexio():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='user',
            password='user',
            database='bot_clima'
        )
        if conn.is_connected():
            print("Connexió establerta a MariaDB.")
        return conn
    except Error as e:
        print(f"Error en connectar-se a MariaDB: {e}")
        return None

# Funció per afegir un nou usuari
def afegir_usuari(conn, id_usuari, nom_usuari, idioma, ciutat_defecte):
    cursor = conn.cursor()
    query = '''
    INSERT INTO usuaris (id_usuari, nom_usuari, idioma, ciutat_defecte)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE nom_usuari = VALUES(nom_usuari), idioma = VALUES(idioma), ciutat_defecte = VALUES(ciutat_defecte)
    '''
    cursor.execute(query, (id_usuari, nom_usuari, idioma, ciutat_defecte))
    conn.commit()

# Funció per afegir una consulta de clima
def afegir_consulta_clima(conn, id_usuari, ciutat, resultat_clima, temperatura, data_hora):
    cursor = conn.cursor()
    query = '''
    INSERT INTO consultes_clima (id_usuari, ciutat, resultat_clima, temperatura, data_hora)
    VALUES (%s, %s, %s, %s, %s)
    '''
    cursor.execute(query, (id_usuari, ciutat, resultat_clima, temperatura, data_hora))
    conn.commit()

# Funció per consultar el clima utilitzant l'API d'OpenWeather
def obtenir_clima(ciutat):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ciutat}&appid={API_KEY_OPENWEATHER}&lang=ca&units=metric'
    resposta = requests.get(url)

    if resposta.status_code == 200:
        dades = resposta.json()
        nom_ciutat = dades['name']
        temperatura = dades['main']['temp']
        descripcio = dades['weather'][0]['description']
        return f"El clima a {nom_ciutat} és {descripcio} amb una temperatura de {temperatura}°C.", temperatura, descripcio
    else:
        return "No s'ha pogut obtenir el clima per la ciutat especificada.", None, None

# Funció per gestionar la comanda /start al bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Envia'm el nom d'una ciutat i t'enviaré el clima actual.")

# Funció per gestionar la consulta del clima
async def consultar_clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ciutat = ' '.join(context.args)
    
    if ciutat:
        clima, temperatura, descripcio = obtenir_clima(ciutat)
        await update.message.reply_text(clima)

        # Connexió a la base de dades
        conn = crear_connexio()
        if conn:
            id_usuari = update.message.from_user.id
            nom_usuari = update.message.from_user.username or 'Desconegut'
            idioma = 'ca'  # O pots detectar l'idioma de l'usuari
            afegir_usuari(conn, id_usuari, nom_usuari, idioma, ciutat)
            afegir_consulta_clima(conn, id_usuari, ciutat, descripcio, f"{temperatura}°C", update.message.date)
            conn.close()
    else:
        await update.message.reply_text("Si us plau, introdueix el nom d'una ciutat.")

# Configuració del bot
async def main():
    # Inicialitzar l'aplicació del bot de Telegram
    application = ApplicationBuilder().token(API_KEY_TELEGRAM).build()

    # Comandes del bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clima", consultar_clima))

    # Comença el bot
    await application.start()
    await application.idle()

# Executar el bot
import asyncio
asyncio.run(main())