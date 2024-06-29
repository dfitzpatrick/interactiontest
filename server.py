from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
import logging
import uvicorn
from logging import StreamHandler
import contextlib
import discord
from discord.ext import commands
from discord import ui, app_commands
import logging
from typing import TypedDict, AsyncIterator
from dotenv import load_dotenv
import sys
import os
from starlette.responses import PlainTextResponse, JSONResponse, Response
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
load_dotenv()



logging.basicConfig(
    format="%(asctime)s | %(name)25s | %(funcName)25s | %(levelname)6s | %(message)s",
    datefmt="%b %d %H:%M:%S",
    level=logging.DEBUG,
    handlers=[StreamHandler(stream=sys.stdout)]
)
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('asyncpg').setLevel(logging.DEBUG)
log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents, **kwargs)



class State(TypedDict):
    bot:  Bot

async def verify_signature(request: Request) -> bool:
    try:
        sig = request.headers['X-Signature-Ed25519']
        stamp = request.headers['X-Signature-Timestamp']
        body = (await request.body()).decode('utf-8')
        verify_key = VerifyKey(bytes.fromhex(os.environ['PUBLIC_KEY']))
        verify_key.verify(f'{stamp}{body}'.encode(), bytes.fromhex(sig))
        return True
    except (KeyError, BadSignatureError):
        return False

async def interaction(request: Request):
    verified = await verify_signature(request)
    if not verified:
        return Response(status_code=401)
    
    data = await request.json()
    log.debug(data)
    response = {'type': 1}
    log.debug(f"Responding: {response}")
    return JSONResponse(response)
    


class MyView(ui.View):

    @ui.button(label="Click Me")
    async def button_click(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content=f"{interaction.user.name} clicked the button")


intents = discord.Intents.default()
intents.members = True
bot = Bot(intents=intents)

@bot.tree.command()
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True)
async def usercmdtest(interaction: discord.Interaction) -> None:
    await interaction.response.send_message('test', view=MyView())





@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[State]:
    global bot
    async with bot:
        log.debug('logging into discord')
        await bot.login(os.environ['TOKEN'])
        yield {"bot": bot}

app = Starlette(debug=True, lifespan=lifespan, routes=[
    Route('/interactions', interaction, methods=["GET", "POST"])
])

if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)
