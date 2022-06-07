from asyncio import sleep
from datetime import timedelta
from os import remove
from random import choice
from string import ascii_letters
from time import time
from traceback import format_exc

from aiofiles import open as aopen
from pyrogram import filters
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    PeerIdInvalid,
    UserIsBlocked,
)
from pyrogram.types import Message

from vidmergebot.bot_class import VidMergeBot
from vidmergebot.db import MainDB
from vidmergebot.vars import Vars

broadcast_ids = {}


async def send_msg(user_id: int, m: Message):
    try:
        await m.forward(chat_id=user_id)
        return 200, None
    except FloodWait as e:
        await sleep(e.value)
        return send_msg(user_id, m)
    except InputUserDeactivated:
        return 400, f"{user_id}: deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id}: blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id}: user id invalid\n"
    except Exception as ef:
        return 500, f"{user_id}: {ef}\n{format_exc()}\n"


@VidMergeBot.on_message(
    filters.private
    & filters.command("broadcast")
    & filters.user(Vars.OWNER_ID)
    & filters.reply,
)
async def broadcast_(_, m: Message):
    all_users = MainDB.get_all_users()
    broadcast_msg = m.reply_to_message
    while True:
        broadcast_id = "".join(choice(ascii_letters) for _ in range(3))
        if not broadcast_ids.get(broadcast_id):
            break
    out = await m.reply_text(
        text="Broadcast Started! You will be notified with log file when all the users are notified.",
    )
    start_time = time()
    total_users = MainDB.total_users_count()
    done = 0
    failed = 0
    success = 0
    broadcast_ids[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success,
    )
    async with aopen("broadcast.txt", "w") as broadcast_log_file:
        for user in all_users:
            if user == Vars.BOT_ID:
                continue
            sts, msg = await send_msg(user_id=int(user), m=broadcast_msg)
            if msg is not None:
                await broadcast_log_file.write(msg)
            if sts == 200:
                success += 1
            else:
                failed += 1
            if sts == 400:
                MainDB.delete_user(user)
            done += 1
            if broadcast_ids.get(broadcast_id) is None:
                break
            broadcast_ids[broadcast_id].update(
                dict(current=done, failed=failed, success=success),
            )
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = timedelta(seconds=int(time() - start_time))
    await sleep(3)
    await out.delete()
    if failed == 0:
        await m.reply_text(
            text=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True,
        )
    else:
        await m.reply_document(
            document="broadcast.txt",
            caption=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True,
        )
    remove("broadcast.txt")
