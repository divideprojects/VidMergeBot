from platform import python_version
from time import gmtime, strftime, time

import pyromod.listen  # skipcq:PYL-W0611
from pyrogram import Client, __version__
from pyrogram.raw.all import layer

from vidmergebot import LOGGER, UPTIME
from vidmergebot.vars import Vars

# Check if MESSAGE_DUMP is correct
if Vars.MESSAGE_DUMP == -100 or not str(Vars.MESSAGE_DUMP).startswith("-100"):
    raise Exception(
        "Please enter a vaild Supergroup ID, A Supergroup ID starts with -100",
    )


class VidMergeBot(Client):
    """Starts the Pyrogram Client on the Bot Token when we do 'python3 -m alita'"""

    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name,
            bot_token=Vars.BOT_TOKEN,
            plugins=dict(root=f"{name}.plugins"),
            api_id=Vars.APP_ID,
            api_hash=Vars.API_HASH,
            workers=Vars.WORKERS,
        )

    async def start(self):
        """Start the bot."""
        await super().start()

        # Get my info
        meh = await self.get_me()
        LOGGER.info("Starting bot...")

        # Show in Log that bot has started
        LOGGER.info(
            f"Pyrogram v{__version__} (Layer - {layer}) started on @{meh.username}!",
        )
        LOGGER.info(f"Python Version: {python_version()}\n")
        LOGGER.info("Bot Started Successfully!\n")

    async def stop(self, **kwargs):
        """Stop the bot and send a message to MESSAGE_DUMP telling that the bot has stopped."""
        runtime = strftime("%Hh %Mm %Ss", gmtime(time() - UPTIME))
        await super().stop()
        LOGGER.info(
            f"""Bot Stopped.
            Runtime: {runtime}s\n
        """,
        )
