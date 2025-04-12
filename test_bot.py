# test_bot.py
import twitchio
from twitchio.ext import commands
import os
import logging
from dotenv import load_dotenv

import asyncio
import sys
# Add this block near the top, after imports, before twitchio/dotenv
if sys.platform == 'win32':
     print("Platform is Windows, setting asyncio policy to WindowsSelectorEventLoopPolicy")
     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# --- Rest of the script ---

# --- 1. Cargar Variables de Entorno ---
# Asegúrate de que tu archivo .env está en el mismo directorio
try:
    load_dotenv()
    print("Archivo .env cargado (o intentado cargar).")
except Exception as e:
    print(f"Advertencia: No se pudo cargar dotenv. ¿Existe el archivo .env? Error: {e}")

# --- 2. Configurar Logging ---
# Usamos DEBUG para obtener la máxima información durante la prueba
#logging.basicConfig(level=logging.DEBUG)
#print("Logging configurado a nivel DEBUG.")

# --- 3. Obtener Credenciales ---
TWITCH_TOKEN = os.getenv('TWITCH_TOKEN')
TWITCH_NICK = os.getenv('TWITCH_NICK')
TWITCH_CHANNEL = os.getenv('TWITCH_CHANNEL')

# --- 4. Comprobar Credenciales Esenciales ---
if not all([TWITCH_TOKEN, TWITCH_NICK, TWITCH_CHANNEL]):
     # Si falta alguna credencial, imprime un error claro y sale
     print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
     print("!!! ERROR FATAL: Faltan credenciales de Twitch en .env     !!!")
     print("!!! Asegúrate de que TWITCH_TOKEN, TWITCH_NICK y         !!!")
     print("!!! TWITCH_CHANNEL están definidos en tu archivo .env    !!!")
     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
     exit() # Salir del script si faltan datos
else:
    # Confirma que las credenciales (al menos) existen
    print("Credenciales TWITCH_TOKEN, TWITCH_NICK, TWITCH_CHANNEL encontradas en el entorno.")
    # Una pequeña ofuscación para no mostrar todo el token en logs si se copian/pegan
    print(f"Usando Nick: {TWITCH_NICK}, Canal: {TWITCH_CHANNEL}, Token: oauth:***{TWITCH_TOKEN[-6:] if TWITCH_TOKEN and len(TWITCH_TOKEN) > 10 else 'INVALIDO'}")

# --- 5. Inicializar el Bot ---
# La configuración más básica posible
try:
    bot = commands.Bot(
        token=TWITCH_TOKEN,
        nick=TWITCH_NICK,
        prefix='!', # Necesario, aunque no definamos comandos aquí
        initial_channels=[TWITCH_CHANNEL] # Intenta unirse al canal especificado
    )
    print("Objeto bot de twitchio inicializado.")
except Exception as e:
    print(f"!!!!!!!!!! ERROR al inicializar commands.Bot: {repr(e)} !!!!!!!!!!")
    exit() # Salir si la inicialización del bot falla

# --- 6. Definir el Evento 'ready' ---
# Este es el evento clave que estamos probando
@bot.event()
async def event_ready():
    # La acción más simple posible: imprimir mensajes claros
    print("\n==========================================")
    print("=== ¡¡¡ MINIMAL BOT: event_ready SE EJECUTÓ !!! ===")
    print(f"=== Conectado como: {bot.nick}        ===")
    print(f"=== Canal objetivo: {TWITCH_CHANNEL}      ===")
    print("==========================================\n")
    # Si ves esto, ¡el evento funciona!
@bot.event()
async def event_message(message):
    print(message.content)
# --- 7. Definir el Evento 'join' (Opcional pero útil) ---
# Para confirmar que el bot se une al canal
@bot.event()
async def event_join(channel: twitchio.Channel, user: twitchio.User):
    # Comprueba si el usuario que se unió es el propio bot
    if user.name.lower() == bot.nick.lower():
        print(f"\n--- MINIMAL BOT: Evento JOIN detectado. Bot se unió al canal #{channel.name} ---\n")

# --- 8. Ejecutar el Bot ---
print(f"\n--- MINIMAL BOT: Todo configurado. Llamando a bot.run() para iniciar conexión... ---")
print(f"--- (Esperando conexión y evento 'ready'...) ---")


try:
    # Esta llamada bloquea y mantiene el bot corriendo
    bot.run()
except Exception as e:
    # Captura cualquier error que ocurra durante bot.run()
    print(f"\n!!!!!!!!!! ERROR CRÍTICO durante bot.run(): {repr(e)} !!!!!!!!!!\n")

# --- 9. Mensaje Final (No debería alcanzarse normalmente) ---
# Si el bot funciona correctamente, bot.run() no debería terminar.
# Si ves este mensaje, algo hizo que bot.run() se detuviera.
print("\n--- MINIMAL BOT: bot.run() ha terminado. Esto es inesperado si la conexión fue exitosa. ---")