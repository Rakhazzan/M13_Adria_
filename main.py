

import logging # Importa el mòdul de registre (logging)
import requests # Importa el mòdul per fer peticions HTTP
import mariadb # Importa el connector per a la base de dades MariaDB
from telegram import Update # Importa l'objecte Update del bot de Telegram
from telegram.ext import ( # Importa els gestors de comandes i missatges del bot 
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Configura el registre per mostrar missatges en format un format
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Estableix el nivell de registre de "httpx" a advertència (warning)
logging.getLogger("httpx").setLevel(logging.WARNING)
# Crea un logger per aquest modul
logger = logging.getLogger(__name__)
# Defineix un estat de la conversa per demanar la ciutat
CITY = range(1)
# Intenta connectar-se a la base de dades MariaDB
try:
        conn = mariadb.connect(
        user="user1", # Usuari de la base de dades
        password="user1", # Contrasenya de l'usuari
        host="127.0.0.1", # Host de la base de dades
        port=3306, # Port de connexió
        database="TelegramBot" # Nom de la base de dades

        )
        cur = conn.cursor() # Crea un cursor per executar consultes
except mariadb.Error as e: # Agafa errors de connexió
        print(f"Error connecting to MariaDB Platform: {e}")

   
        
# Funció per iniciar la conversa amb l'usuari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
   # Envia un missatge a l'usuari demanant el nom de la ciutat
    await update.message.reply_text("Please, enter a city name to get the current wheater. ")
    logger.info("Waiting for city ") # Registra  la ciutat
    return CITY

# Funció per processar la ciutat introduida per l'usuari
async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
   
    user = update.message.from_user # Obte informació de l'usuari
    logger.info("City ask from %s: %s", user.first_name, update.message.text) # Registra la ciutat demanada
    text = update.message.text if update.message else update.channel_post.text # Obté el text del missatge
    city = text # Guarda el nom de la ciutat

    # URL de l'API de temps per obtenir la informació de la ciutat
    url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid=ea52380432635267ca37ed8561641ad1'.format(city)

    res = requests.get(url) # Fa una peticio a l'API
    data = res.json() # Converteix la resposta en un JSON
    if data['cod'] == "404": # Si no es troba la ciutat, envia un missatge d'error
         await context.bot.send_message(chat_id=update.effective_chat.id, text=('City not found'))
    
    else:
        # Inserta la ciutat i l'usuari a la base de dades
        query = "INSERT INTO users (User, city) VALUES (%s,%s)"
        value_tuple=(user.first_name,city);
        cur.execute(query, value_tuple)
        conn.commit() # Confirma els canvis a la base de dades
        
        # Obte la informacio meteorologica
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        wind = data['wind']['speed']
        description = data['weather'][0]['description']
        temp = data['main']['temp']
    
        # Envia missatges a l'usuari amb la informació del temps
        await context.bot.send_message(chat_id=update.effective_chat.id, text=('Temperature: ' + str (temp) + ' Celcius degrees in the city of ' + city))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=('Wind: ' + str(wind) + ' Pressure ' + str(pressure )))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=('Humidity: ' +str(humidity) + ' Description ' + description ))
    

    return ConversationHandler.END # Finalitza la conversa

# Funció asíncrona per cancel·lar la conversa
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
   
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name) # Registra quan cancela
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.")

    return ConversationHandler.END # Acaba la conversa

# Funcio principal del bot
def main() -> None:
   
   # Crea l'aplicació del bot amb el token d'autenticació
    application = Application.builder().token("7750424681:AAHBQ8BGfHf6-pv2r6dWY9Gos0OzGnYLXcc").build()

    
     #Defineix un gestor de converses amb els punts d'entrada 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)], # Comença amb la comanda /start
        states={
            CITY: [MessageHandler(filters.TEXT, city)], # Gestiona el text que introdueix l'usuari
        },
        fallbacks=[CommandHandler("cancel", cancel)], # Permet cancel·lar la conversa amb /cancel
    )

    application.add_handler(conv_handler)

   # Executa el bot en mode de polling per mirar si hi han actualitzacions 
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# Per iniciar el bot
if __name__ == "__main__":
    main()