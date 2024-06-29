import discord
from discord.ext import commands
from discord import ui
import logging
intents = discord.Intents.default()
intents.members = True

log = logging.getLogger(__name__)

class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents, **kwargs)

    async def on_ready(self):
        log.debug(f'Logged on as {self.user} (ID: {self.user.id})')

bot = Bot(intents=intents)

class MyView(ui.View):

    @ui.button(label="Click Me")
    async def button_click(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content=f"{interaction.user.name} clicked the button")


# write general commands here
@commands.check(commands.is_owner())
@commands.command()
async def sync(ctx: commands.Context) -> None:
    await bot.tree.sync()

@bot.tree.command()
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True)
async def usercmdtest(interaction: discord.Interaction) -> None:
    await interaction.response.send_message('test', view=MyView())

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--sync', action='store_true')
args = parser.parse_args()