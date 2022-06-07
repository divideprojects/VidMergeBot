from pyrogram.types import Message

from vidmergebot.utils.ikb import ikb
from vidmergebot.vars import Vars


class Constants:
    @staticmethod
    async def join_channel_msg(m: Message):
        join_channel = Vars.AUTH_CHANNEL.replace("@", "")
        return await m.reply_text(
            "You have reached your limit of usage."
            "\nPlease wait for some time before using this bot again."
            f"\nIf you want to increase the usage limit, join {Vars.AUTH_CHANNEL}",
            reply_markup=ikb(
                [[("Join Channel", f"https://t.me/{join_channel}", "url")]],
            ),
        )

    @staticmethod
    def ban_kb(user_id: int):
        return (
            ikb(
                [[("Ban User", f"ban_{user_id}")]],
            )
            if user_id != Vars.OWNER_ID
            else None
        )

    start_kb = [
        [
            ("How to use", "help_callback.start"),
            ("Help & Support", f"https://t.me/{Vars.SUPPORT_GROUP}", "url"),
        ],
    ]
    page1_help_kb = [[(">>>", "help_callback.page2")]]
    page2_help_kb = [[("<<<", "help_callback.page1")]]

    support_kb = ikb(
        [
            [
                (
                    "Support Group",
                    f"https://t.me/{Vars.SUPPORT_GROUP}",
                    "url",
                ),
                (
                    "Bots Channel",
                    "https://t.me/DivideProjects",
                    "url",
                ),
            ],
        ],
    )

    start_msg = """
Hi {}, I am Video Merger Bot!

<b>How to Merge multiple Videos?</b>
<b>Usage:</b> Send me one video, then send me another video after that and press the \
merge button to start the process!

{}
"""

    page1_help = """
<b><u>Commands:</b></u>
/start: <i>Start the bot.</i>
/help: <i>Show this message.</i>

Just send me minimum 2 videos and I'll merge them for you!
"""

    page2_help = """
<b><u>FAQs</b></u>:

<b>• Why is bot slow?</b>
- <i>Bot is hosted on free heroku server, which ultimately makes it slow.</i>

<b>• Why is bot always busy?</b>
- <i>The bot can only process 1 video at a time, check 1st FAQ to know why.</i>

<b>• Why does the video size increase?</b>
- <i>The bot currently uses ultrafast algorithm of ffmpeg which results in higher file sizes, 1st FAQ to know more.</i>

<b>• Is NSFW allowed on Bot?</b>
- <i>No, any user found uploading and using NSFW Videos on Bot will be banned infinitely</i>

<b>• Why will happen if file size becomes more than 2GB?</b>
- <i>The video will be uploaded to streamtape and bot will send a link to you.</i>

<b>• Why is there a restriction of 5 minutes?</b>
- <i>For now bot is providing every services for free and that could be misused by spammers so inorder to maintain a stable performance all of the users are limited</i>
"""

    progress_msg = """
Percentage : {0}%
Done ✅: {1}
Total 🌀: {2}
Speed 🚀: {3}/s
ETA 🕰: {4}
"""
