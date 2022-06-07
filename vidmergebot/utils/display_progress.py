from asyncio import sleep
from math import floor
from time import time
from traceback import format_exc

from pyrogram.errors import MessageNotModified

from vidmergebot import LOGGER
from vidmergebot.utils.constants import Constants


async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time()
    diff = now - start
    # print(f"{current}/{total}")
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{}{}] \n".format(
            "".join("●" for _ in range(floor(percentage / 5))),
            "".join("○" for _ in range(20 - floor(percentage / 5))),
        )

        tmp = progress + Constants.progress_msg.format(
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != "" else "0 s",
        )
        try:
            await message.edit(text=f"<b>{ud_type}</b>\n\n{tmp}")
        except MessageNotModified:
            await sleep(1.5)
        except Exception as ef:
            LOGGER.error(ef)
            LOGGER.error(format_exc())


def humanbytes(size: int or str):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + "B"


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
        + ((str(milliseconds) + "ms, ") if milliseconds else "")
    )
    return tmp[:-2]
