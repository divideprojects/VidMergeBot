from datetime import datetime
from logging import INFO, WARNING, FileHandler, StreamHandler, basicConfig, getLogger
from os import mkdir, path
from sys import exit as sysexit
from sys import stdout, version_info
from time import time
from traceback import format_exc

LOG_DATETIME = datetime.now().strftime("%d_%m_%Y-%H_%M_%S")
LOGDIR = f"{__name__}/logs"

# Make Logs directory if it does not exixts
if not path.isdir(LOGDIR):
    mkdir(LOGDIR)

basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=INFO,
    handlers=[
        FileHandler(filename=f"{LOGDIR}/{__name__}_{LOG_DATETIME}.log"),
        StreamHandler(stdout),
    ],
)

getLogger("pyrogram").setLevel(WARNING)
LOGGER = getLogger(__name__)

# if version < 3.9, stop bot.
if version_info[0] < 3 or version_info[1] < 7:
    LOGGER.error(
        (
            "You MUST have a Python Version of at least 3.7!\n"
            "Multiple features depend on this. Bot quitting."
        ),
    )
    sysexit(1)  # Quit the Script

# the secret configuration specific things
try:
    from .vars import Vars
except Exception as ef:
    LOGGER.error(ef)  # Print Error
    LOGGER.error(format_exc())
    sysexit(1)

LOGGER.info("------------------------")
LOGGER.info("|      VidMergeBot     |")
LOGGER.info("------------------------")
LOGGER.info(f"Version: {Vars.VERSION}")
LOGGER.info(f"Owner: {str(Vars.OWNER_ID)}\n")

# Account Related
STREAMTAPE_DEFAULT = Vars.STREAMTAPE_DEFAULT
UPTIME = time()  # Check bot uptime
