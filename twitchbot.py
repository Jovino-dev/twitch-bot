from twitchio.ext import commands
import openai

# Configuración de OpenAI
openai.api_key = "TU_API_KEY_DE_OPENAI"

# Configuración del bot de Twitch
class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token="TU_TOKEN_DE_TWITCH", prefix="!", initial_channels=["tu_canal"])

    async def event_ready(self):
        print(f"Bot conectado como {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        # Envía el mensaje del chat a OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.content}]
        )

        # Responde al chat con el texto de OpenAI
        await message.channel.send(response['choices'][0]['message']['content'])

# Inicia el bot
bot = Bot()
bot.run()
