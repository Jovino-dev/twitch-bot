import logging
import os
import twitchio
from twitchio.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
import sys
import random
from collections import deque # <--- Importar deque

print("--- EJECUTANDO VERSIÓN MÁS RECIENTE DEL SCRIPT (con historial) ---")

# Forzar política asyncio en Windows
if sys.platform == 'win32':
     print("Plataforma es Windows, estableciendo política asyncio a WindowsSelectorEventLoopPolicy.")
     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Cargar variables de entorno
load_dotenv(override=True)
#logging.basicConfig(level=logging.INFO)

# --- Constantes y Variables Globales ---
PROACTIVE_MIN_MESSAGES = 5
PROACTIVE_MAX_MESSAGES = 10
PERSONA_FILENAME = "persona.txt"
HISTORY_MAX_LENGTH = 10 # <--- Número máximo de mensajes a recordar

message_counter = 0
proactive_target_count = 0
chatted_users = set()
bot_persona = ""
# Usamos deque para mantener automáticamente solo los últimos N mensajes
chat_history = deque(maxlen=HISTORY_MAX_LENGTH) # <--- Inicializar deque para historial

# --- Cargar Personalidad del Bot desde Archivo Externo ---
try:
    with open(PERSONA_FILENAME, 'r', encoding='utf-8') as f:
        bot_persona = f.read().strip()
    if not bot_persona:
        print(f"ADVERTENCIA: El archivo '{PERSONA_FILENAME}' está vacío.")
    
        print(f"Personalidad del bot cargada desde '{PERSONA_FILENAME}'.")
except FileNotFoundError:
    print(f"!!! ERROR FATAL: No se encontró el archivo '{PERSONA_FILENAME}'. !!!")
    exit()
except Exception as e:
    print(f"!!!!!!!!!! ERROR al leer el archivo '{PERSONA_FILENAME}': {repr(e)} !!!!!!!!!!")
    exit()

# Configurar API de Gemini
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        system_instruction=bot_persona
    )
    print("Modelo Gemini configurado correctamente con Instrucción de Sistema desde archivo.")
except Exception as e:
    print(f"Error configurando Gemini: {e}")
    exit()

# Configurar Bot de Twitch
try:
    bot = commands.Bot(
        token=os.getenv('TWITCH_TOKEN'),
        nick=os.getenv('TWITCH_NICK'),
        prefix='!',
        initial_channels=[os.getenv('TWITCH_CHANNEL')]
    )
    print("Objeto bot de twitchio inicializado.")
except Exception as e:
    print(f"!!!!!!!!!! ERROR al inicializar commands.Bot: {repr(e)} !!!!!!!!!!")
    exit()

# --- Función Helper para Formatear Historial ---
def format_chat_history(history_deque: deque) -> str:
    """Convierte el deque de historial en un string formateado para el prompt."""
    if not history_deque:
        return "No hay historial reciente."
    # Formato: "Usuario1: Mensaje1\nUsuario2: Mensaje2\n..."
    return "\n".join([f"{msg['author']}: {msg['content']}" for msg in history_deque])

# --- Evento Ready ---
@bot.event()
async def event_ready():
    global proactive_target_count
    print("--- DEBUG: Entrando en event_ready ---")
    try:
        channel_name = os.getenv("TWITCH_CHANNEL")
        if bot.nick and channel_name:
             print(f'🤖 ¡Bot conectado como {bot.nick} al canal {channel_name}!')
             proactive_target_count = random.randint(PROACTIVE_MIN_MESSAGES, PROACTIVE_MAX_MESSAGES)
             print(f"--- INFO: Bot hablará proactivamente después de {proactive_target_count} mensajes. ---")
             print("--- Bot listo y esperando mensajes ---")
        else:
             print("⚠️ Error: No se pudo obtener nick del bot o nombre del canal en event_ready.")
    except Exception as e:
        print(f"!!!!!!!!!! ERROR DENTRO DE event_ready: {repr(e)} !!!!!!!!!!!")
    print("--- DEBUG: Saliendo de event_ready ---")

# --- Evento Message ---
@bot.event()
async def event_message(message):
    global message_counter, proactive_target_count, chatted_users, chat_history

    # 1. Ignorar mensajes propios o sin autor
    if message.echo or message.author is None:
        return

    # 2. Añadir usuario a la memoria
    chatted_users.add(message.author.name.lower())

    # 3. Añadir mensaje al historial (autor y contenido)
    # Guardamos antes de filtrar comandos para que el historial sea más completo
    chat_history.append({'author': message.author.name, 'content': message.content})
    # print(f"DEBUG: Historial: {list(chat_history)}") # Descomentar para depurar historial

    # 4. Incrementar contador si no es comando
    if not message.content.startswith('!'):
        message_counter += 1

    # --- Construir el contexto del historial ---
    history_context_string = f"--- Inicio Historial Reciente (Máx {HISTORY_MAX_LENGTH} mensajes) ---\n"
    history_context_string += format_chat_history(chat_history)
    history_context_string += "\n--- Fin Historial Reciente ---"
    # --- Fin Construcción Contexto ---


    # 5. Comprobar Mención
    bot_mentioned = f"@{bot.nick.lower()}"
    if bot_mentioned in message.content.lower():
        user_query = message.content.replace(bot_mentioned, "").strip()
        print(f"INFO: Recibida mención de '{message.author.name}'. Query: '{user_query}'")
        if not user_query: return

        # Prompt para Gemini incluyendo historial y la mención específica
        prompt_for_gemini = f"{history_context_string}\n\nBasándote en el historial anterior si es relevante, responde a esto:\nEl usuario de Twitch '{message.author.name}' te dice: '{user_query}'"

        print(f"DEBUG: Enviando a Gemini (mención con historial):\n{prompt_for_gemini}\n---")
        try:
            response = await model.generate_content_async(prompt_for_gemini)
            bot_response = response.text
            if len(bot_response) > 480: bot_response = bot_response[:480] + "..."
            print(f"DEBUG: Respuesta de Gemini (mención): \"{bot_response}\"")
            await message.channel.send(f"@{message.author.name} {bot_response}")
        except Exception as e:
            print(f"ERROR: Error en Gemini/envío (mención): {repr(e)}")

    # 6. Comprobar Chat Proactivo (si no hubo mención)
    elif message_counter >= proactive_target_count:
        print(f"INFO: Alcanzado umbral proactivo ({message_counter}/{proactive_target_count}). Generando mensaje...")

        # Prompt proactivo incluyendo historial
        proactive_prompt_base = "Actúa como Happy_Hobino_Machino. Escribe un comentario corto y amigable, o una pregunta abierta para el chat de Twitch para fomentar la conversación. Sé natural y encaja con el ambiente del stream."
        prompt_for_gemini = f"{history_context_string}\n\nBasándote en el historial anterior si es relevante:\n{proactive_prompt_base}"

        print(f"DEBUG: Enviando a Gemini (proactivo con historial):\n{prompt_for_gemini}\n---")
        try:
            response = await model.generate_content_async(prompt_for_gemini)
            bot_response = response.text
            if len(bot_response) > 480: bot_response = bot_response[:480] + "..."

            if bot_response and bot.nick.lower() not in bot_response.lower():
                print(f"DEBUG: Respuesta de Gemini (proactivo): \"{bot_response}\"")
                await message.channel.send(bot_response)
            else:
                 print(f"WARN: Respuesta proactiva de Gemini vacía o contenía auto-mención. No se envió.")
        except Exception as e:
            print(f"ERROR: Error en Gemini/envío (proactivo): {repr(e)}")
        finally:
            message_counter = 0
            proactive_target_count = random.randint(PROACTIVE_MIN_MESSAGES, PROACTIVE_MAX_MESSAGES)
            print(f"INFO: Contador reiniciado. Próximo mensaje proactivo después de {proactive_target_count} mensajes.")

# --- Evento Join ---
# (Sin cambios)
@bot.event()
async def event_join(channel: twitchio.Channel, user: twitchio.User):
     if user.name.lower() == bot.nick.lower():
        print(f"✅ *** Bot se ha UNIDO exitosamente al canal: {channel.name} ***")

# --- Bloque Principal ---
# (Sin cambios relevantes, solo asegurarnos de que la comprobación de bot_persona está)
if __name__ == "__main__":
    print("--- Valores de Configuración ---")
    print(f"Nick: {os.getenv('TWITCH_NICK')}")
    print(f"Canal: {os.getenv('TWITCH_CHANNEL')}")
    print(f"Token empieza con 'oauth:': {os.getenv('TWITCH_TOKEN', '').startswith('oauth:')}")
    print(f"Clave Gemini existe: {bool(os.getenv('GEMINI_API_KEY'))}")
    print(f"Archivo de Personalidad: '{PERSONA_FILENAME}'")
    print(f"Historial a recordar: {HISTORY_MAX_LENGTH} mensajes") # <-- Añadido
    print("--- Intentando conectar a Twitch ---")

    if not bot_persona:
         print("ERROR FATAL: La personalidad del bot no se pudo cargar o está vacía.")
    elif not all([...]): # Puse '...' aquí, asegúrate que tu comprobación original esté completa
        print("Error: Faltan variables de entorno...")
    else:
        try:
            bot.run()
        except Exception as e:
             print(f"!!!!!!!!!! ERROR CRÍTICO durante bot.run(): {repr(e)} !!!!!!!!!!")