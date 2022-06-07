from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from pyrogram.types import Message

from vidmergebot import Vars
from vidmergebot.db import MainDB
from vidmergebot.utils.constants import Constants


def joinCheck():
    def wrapper(func):
        async def decorator(c: Client, m: Message):
            if not Vars.LIMIT_USER_USAGE:
                return await func(c, m)
            if m.sender_chat:
                return

            user_id = m.from_user.id
            db = MainDB(user_id)
            today_usage = db.get_usage()

            try:
                get = await c.get_chat_member(Vars.AUTH_CHANNEL, user_id)
            except UserNotParticipant:
                if today_usage >= Vars.MAX_NON_JOIN_USAGE:
                    return await Constants.join_channel_msg(m)
            else:
                if get.status in (ChatMemberStatus.RESTRICTED, ChatMemberStatus.BANNED):
                    return await m.reply_text(
                        f"You were banned from using me. If you think this is a mistake then report this at {Vars.SUPPORT_GROUP}",
                    )
                if (
                    get.status
                    not in (
                        ChatMemberStatus.OWNER,
                        ChatMemberStatus.ADMINISTRATOR,
                        ChatMemberStatus.MEMBER,
                    )
                    and today_usage >= Vars.MAX_JOIN_USAGE
                ):
                    return await Constants.join_channel_msg(m)
            return await func(c, m)

        return decorator

    return wrapper
