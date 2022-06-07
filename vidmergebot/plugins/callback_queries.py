from pyrogram import filters
from pyrogram.types import CallbackQuery

from vidmergebot.bot_class import VidMergeBot
from vidmergebot.vars import Vars


@VidMergeBot.on_callback_query(filters.regex("^btn_not_work$"))
async def btn_not_work_callback(_, q: CallbackQuery):
    await q.answer(
        "Well, this button does not work xD\n\nCheck other buttons!",
        show_alert=True,
    )


@VidMergeBot.on_callback_query(filters.regex("^ban_"))
async def ban_user(c: VidMergeBot, q: CallbackQuery):
    user_id = int(q.data.split("_", 1)[1])
    await c.ban_chat_member(Vars.AUTH_CHANNEL, user_id)
    await q.answer("User Banned from Updates Channel!", show_alert=True)
