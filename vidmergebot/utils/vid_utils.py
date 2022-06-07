from asyncio import create_subprocess_exec, sleep, subprocess
from os import path
from random import randint
from time import time
from traceback import format_exc
from typing import List

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image, ImageDraw, ImageFont
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import Message

from vidmergebot import LOGGER
from vidmergebot.utils.ikb import ikb
from vidmergebot.vars import Vars


async def extract_vid_data(output_vid: str):
    metadata = extractMetadata(createParser(output_vid))
    duration = metadata.get("duration").seconds if metadata.has("duration") else 0
    width = metadata.get("width") if metadata.has("width") else 100
    height = metadata.get("height") if metadata.has("height") else 100
    return duration, width, height


async def gen_ss(
    user_id: int,
    duration: str or int,
    output_vid: str,
    width: str or int,
    height: str or int,
):
    try:
        video_thumbnail = f"{Vars.DOWN_PATH}/{user_id}/{int(time())}.jpg"
        ttl = randint(0, int(duration) - 1)
        file_genertor_command = [
            "ffmpeg",
            "-ss",
            str(ttl),
            "-i",
            output_vid,
            "-vframes",
            "1",
            video_thumbnail,
        ]
        process = await create_subprocess_exec(
            *file_genertor_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        while process.returncode != 0:
            await sleep(1)  # Sleep and wait for ss to be generated

        _, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        if e_response:
            LOGGER.error(e_response)
            LOGGER.error(format_exc())
            return None

        name = "@VidMergeBot"
        Image.open(video_thumbnail).convert("RGB").save(video_thumbnail)
        font = ImageFont.truetype("vidmergebot/fonts/Roboto-Regular.ttf", 120)
        img = Image.open(video_thumbnail)
        draw = ImageDraw.Draw(img)
        w, h = draw.textsize(name, font=font)
        h += int(h * 0.21)
        img.resize((width, height))
        draw.text(((width - w) / 2, (height - h) / 2), name, (0, 191, 255), font=font)
        img.save(video_thumbnail, "JPEG")
        return video_thumbnail
    except Exception as err:
        LOGGER.error(f"Error: {err}")
        LOGGER.error(format_exc())
        return None


async def concat_vids(m: Message, user_id: int, vid_list: List[str], outfile_name: str):
    file_genertor_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        f"inputs_{user_id}.txt",
        "-c",
        "copy",
        outfile_name,
    ]
    process = await create_subprocess_exec(
        *file_genertor_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stats = f"Merging {len(vid_list)} Videos..."

    await m.edit_text(stats)
    while process.returncode != 0:
        await sleep(1)

        if process.returncode == 0:
            break

        try:
            await m.edit(
                text=stats,
                reply_markup=ikb(
                    [[("Cancel ❌", f"cancel_pid.{user_id}.{process.pid}")]],
                ),
            )
        except FloodWait as e:
            await sleep(e.value)
        except MessageNotModified:
            pass

    if path.lexists(outfile_name):
        await m.edit_text("Merged Videos!\nStarting Upload...")
        return outfile_name
    return None
