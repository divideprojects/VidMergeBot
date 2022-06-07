from asyncio import exceptions, sleep
from hashlib import sha1
from os import kill, path
from shutil import rmtree
from time import time

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyromod.helpers import array_chunk, ikb

from vidmergebot import STREAMTAPE_DEFAULT
from vidmergebot.bot_class import VidMergeBot
from vidmergebot.db import MainDB
from vidmergebot.utils.caching import USER_CACHE, block_time, user_cache_reload
from vidmergebot.utils.constants import Constants
from vidmergebot.utils.display_progress import (
    TimeFormatter,
    humanbytes,
    progress_for_pyrogram,
)
from vidmergebot.utils.joinCheck import joinCheck
from vidmergebot.utils.upload_utils import streamtape_upload
from vidmergebot.utils.vid_utils import concat_vids, extract_vid_data, gen_ss
from vidmergebot.vars import Vars

users_files = {"working": False}
bot_id = 1839381674


def make_added_vids_kb(chat_id):
    all_btns = [
        (f"Video {num + 1}", f"video.{key[0]}")
        for num, key in enumerate(users_files[chat_id]["vids"].items())
    ]
    cancel_kb = [("Cancel ❌", f"cancel_add.{chat_id}")]
    if len(all_btns) > 1:
        kb = array_chunk(all_btns, 3)
        kb.append([(f"Merge {len(all_btns)} Videos ✅", "merge_show_options")])
        kb.append(cancel_kb)
    else:
        kb = [cancel_kb]
    return ikb(kb)


# noinspection PyTypeChecker
@VidMergeBot.on_callback_query(filters.regex("^merge_show_options$"))
async def vid_merge_options(_, q: CallbackQuery):
    user_id = q.from_user.id
    if users_files["working"]:
        try:
            _ = users_files[user_id]
            await q.answer("Bot is busy!")
            await q.message.edit_text(
                "Bot is <b>busy</b> right now!!\nPlease try again later...",
                reply_markup=ikb(
                    [
                        [
                            ("Try again 🔄", "merge_show_options"),
                            ("Cancel ❌", f"cancel_add.{user_id}"),
                        ],
                    ],
                ),
            )
        except KeyError:
            await q.message.edit_text("Some error occurred!\nPlease try again.")
        return
    await q.message.edit_text(
        (
            "<b>Choose Upload Type</b>\n\n"
            "<b>📁 File:</b> <i>Send the Merged Video as a Telegram Document</i>\n"
            "<b>🎥 Video:</b> <i>Send the Merged Video as a Telegram Video</i>\n"
            "<b>🌐 Upload to StreamTape:</b> <i>Upload the Video to online website <a href='https://streamtape.com/'>StreamTape</a></i>"
        ),
        disable_web_page_preview=True,
        reply_markup=ikb(
            [
                [("📁 File", "filename_type.file"), ("🎥 Video", "filename_type.video")],
                [("🌐 Upload to StreamTape", "filename_type.streamtape")],
                [
                    ("🔙 Back", "back_all_vids"),
                    ("Cancel ❌", f"cancel_add.{q.from_user.id}"),
                ],
            ],
        ),
    )
    await q.answer("Select a file upload mode!!")
    return


@VidMergeBot.on_callback_query(filters.regex("^filename_type."))
async def set_filename_callback(_, q: CallbackQuery):
    upload_type = q.data.split(".")[1]
    await q.message.edit_text(
        (
            "What should be the name of the file?\n\n"
            "<b>Deafult:</b> The automatic filename set by bot.\n"
            "<b>Custom Filename:</b> Your preferred file name."
        ),
        reply_markup=ikb(
            [
                [
                    ("Default 🤖", f"filename.default.{upload_type}"),
                    ("Custom ✏️", f"filename.custom.{upload_type}"),
                ],
            ],
        ),
    )


@VidMergeBot.on_callback_query(filters.regex("^filename."))
async def enter_filename_callback(c: VidMergeBot, q: CallbackQuery):
    tmp = q.data.split(".")
    user_id = q.from_user.id
    filename_option = tmp[1]
    upload_type = tmp[2]
    if filename_option == "default":
        filename = f"mergedVideo_[{user_id}]_[{int(time())}]_[@DivideProjects].mp4"
        users_files[user_id]["custom_file_name"] = filename
    elif filename_option == "custom":
        await q.message.edit_text(
            "Please send a <b>custom filename</b> to rename file to!\n"
            "Please send a extension with filename as well, they can be: <code>mkv</code>, <code>ts</code>, <code>avi</code>\n"
            "<b>Example:</b> <code>MyMergedVideo.mp4</code>\n\n"
            "If you don't send a file name within 30 seconds, the operation will be <u>cancelled</u>.",
        )
        try:
            filename = await c.listen(user_id, filters=filters.text, timeout=30)
            users_files[user_id]["custom_file_name"] = filename.text
        except exceptions.TimeoutError:
            await q.message.edit_text(
                "User failed to send custom filename\n🚦🚦 Last Process Stopped 🚦🚦",
            )
            users_files["working"] = False
            del users_files[user_id]  # Clear list
            return
    await q.message.delete()
    await q.message.reply_text(
        f"Filename set as <code>{users_files[user_id]['custom_file_name']}</code>\nDo you wish to continue?",
        reply_markup=ikb(
            [
                [
                    ("Yup ✅", f"merge_videos.{upload_type}"),
                    ("Cancel ❌", f"cancel_add.{user_id}"),
                ],
            ],
        ),
    )
    await q.answer("Merging Videos!")


@VidMergeBot.on_message(filters.document | filters.video)
@joinCheck()
async def add_vid(c: VidMergeBot, m: Message):
    chat_id = m.chat.id
    if not m.from_user:
        return
    if m.from_user.id != Vars.OWNER_ID and m.from_user.id in set(
        list(USER_CACHE.keys()),
    ):
        await m.reply_text(
            "Spam protection active!\n"
            f"Please try again after {TimeFormatter((((USER_CACHE[m.from_user.id] + block_time) - time()) * 1000))} minutes",
        )
        return
    try:
        if len(users_files[chat_id]["vids"]) >= Vars.MAX_VIDEOS:
            await m.reply_text(
                f"I can merge maximum {Vars.MAX_VIDEOS} Videos at once",
                reply_markup=make_added_vids_kb(chat_id),
            )
            return
    except KeyError:
        pass

    # Checks if the file is video or not
    if not (m.video or m.document.mime_type.startswith("video/")):
        await m.reply_text(
            "This is not a Video!\nI need a proper Video to add watermark!",
            quote=True,
        )
        return

    if users_files["working"]:
        await m.reply_text(
            "Bot is <b>busy</b> right now!!\nPlease try again later...",
            reply_markup=ikb(
                [
                    [
                        ("Try again 🔄", "merge_show_options"),
                        ("Cancel ❌", f"cancel_add.{m.from_user.id}"),
                    ],
                ],
            ),
        )
        return

    unique_key = sha1(str(m.id).encode("UTF-8")).hexdigest()
    if chat_id in users_files.keys():
        await c.delete_messages(chat_id, message_ids=users_files[chat_id]["last_msg"])
        users_files[chat_id]["vids"][unique_key] = m
    else:
        users_files[chat_id] = {"vids": {unique_key: m}}

    my_msg = await m.reply_text(
        f"Added {len(users_files[chat_id]['vids'])} videos, send another video to start merging.",
        reply_markup=make_added_vids_kb(chat_id),
    )
    users_files[chat_id]["last_msg"] = my_msg.id
    return


@VidMergeBot.on_callback_query(filters.regex("^video."))
async def video_callback_func(_, q: CallbackQuery):
    file_unique_id = q.data.split(".")[1]
    vfile = users_files[q.from_user.id]["vids"][file_unique_id]
    msg_id = vfile
    kb = ikb(
        [
            [("🗑️ Remove File", f"remove_file.{file_unique_id}")],
            [("🔙 Back", "back_all_vids")],
        ],
    )
    vid_num = list(users_files[q.from_user.id]["vids"].keys()).index(file_unique_id) + 1
    file_id = vfile["video"]["file_id"] or vfile["document"]["file_id"]
    await q.message.edit_text(
        f"<a href='tg://openmessage?user_id={bot_id}&message_id={msg_id}'>Video {vid_num}</a>\n<b>File ID</b>: <i>{file_id}</i>",
        reply_markup=kb,
    )
    await q.answer()


@VidMergeBot.on_callback_query(filters.regex("^remove_file."))
async def rem_file_func(_, q: CallbackQuery):
    file_unique_id = q.data.split(".")[1]
    del users_files[q.from_user.id]["vids"][file_unique_id]
    await q.message.edit_text(
        f"Added {len(users_files[q.from_user.id]['vids'])} videos, send another video to start merging.",
        reply_markup=make_added_vids_kb(q.from_user.id),
    )
    await q.answer("Removed file")


@VidMergeBot.on_callback_query(filters.regex("^back_all_vids$"))
async def back_all_vids_func(_, q: CallbackQuery):
    await q.message.edit_text(
        f"Added {len(users_files[q.from_user.id]['vids'])} videos, send another video to start merging.",
        reply_markup=make_added_vids_kb(q.from_user.id),
    )
    await q.answer()


@VidMergeBot.on_callback_query(filters.regex("^cancel_"))
async def cancel_vids_callback(_, q: CallbackQuery):
    cancel_type = q.data.split("_")[1]
    user_id = int(q.data.split(".")[1])

    if cancel_type.startswith("pid"):
        pid = int(q.data.split(".")[2])
        try:
            kill(pid, 9)
        except ProcessLookupError:
            await q.message.edit_text("No Process is running currently!")
            await q.answer("No process running...!")
    await q.message.edit_text("🚦🚦 Last Process Stopped 🚦🚦")
    users_files["working"] = False
    try:
        del users_files[user_id]  # Clear list
    except KeyError:
        pass
    await q.answer("Cancelled Last Process!", show_alert=True)


@VidMergeBot.on_callback_query(filters.regex("^merge_videos."))
async def merge_callback_func(c: VidMergeBot, q: CallbackQuery):
    await user_cache_reload(q)  # Add user to restriction list
    download_link: str = ""
    merge_option = q.data.split(".")[1]
    chat_id = q.from_user.id
    userdb = MainDB(chat_id)
    inputs = []
    all_videos = users_files[chat_id]["vids"]
    await q.message.delete()
    editable = await q.message.reply_text(
        "<b><i>Downloading videos to my local storage...</b></i>",
    )
    try:
        for num, file_unique_id in enumerate(all_videos):
            await sleep(3)
            c_time = time()
            msg = all_videos[file_unique_id]
            fil_loc = await c.download_media(
                msg,
                file_name=f"{Vars.DOWN_PATH}/{chat_id}/",
                progress=progress_for_pyrogram,
                progress_args=(
                    f"<b>Downloading Video {num + 1}/{len(all_videos)}</b>",
                    editable,
                    c_time,
                ),
            )
            await sleep(3)
            inputs.append(fil_loc)  # Append data list
    except RuntimeError:
        await editable.edit_text(
            "You sent another video while merging current videos!\nTry again!",
        )
        return

    # write all files to inputs_$userid.txt
    with open(f"inputs_{chat_id}.txt", "w") as arq:
        arq.write("\n".join(f"file '{i}'" for i in inputs))

    users_files["working"] = True

    outfile_name = (
        f"{Vars.DOWN_PATH}/{chat_id}/{users_files[chat_id]['custom_file_name']}"
    )
    outfile_name = await concat_vids(
        m=editable,
        user_id=chat_id,
        vid_list=users_files[chat_id]["vids"],
        outfile_name=outfile_name,
    )
    users_files["working"] = False

    if outfile_name is None:
        await q.message.reply_text(
            "Some error occurred, please report in my support group!",
        )
        return

    # works fine till here.....

    duration, width, height = await extract_vid_data(outfile_name)
    video_thumbnail = await gen_ss(
        user_id=chat_id,
        duration=duration,
        output_vid=outfile_name,
        width=width,
        height=height,
    )

    file_size = path.getsize(outfile_name)
    file_name = outfile_name.split("/")[-1]
    if STREAMTAPE_DEFAULT or int(file_size) >= 2097152000:
        download_link = await streamtape_upload(
            editable,
            outfile_name,
            file_size,
            video_thumbnail,
        )
    else:
        caption = (
            f"{len(all_videos)} Videos merged successfully!\n"
            f"<b>File Name:</b> <code>{users_files[chat_id]['custom_file_name']}</code>\n"
            f"<b>Size:</b> <code>{humanbytes(file_size)}</code>"
            f"\n\n{Vars.CAPTION}"
        )
        await sleep(3)
        if merge_option in ("file", "video", "streamtape"):
            c_time = time()
            if merge_option == "file":
                dl = await c.send_document(
                    chat_id,
                    outfile_name,
                    caption=caption,
                    reply_markup=Constants.support_kb,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "<b>Uploading Video as a file...</b>",
                        editable,
                        c_time,
                    ),
                    thumb=video_thumbnail,
                )
                download_link = dl.document.file_id
            elif merge_option == "video":
                dl = await c.send_video(
                    chat_id,
                    outfile_name,
                    caption=caption,
                    reply_markup=Constants.support_kb,
                    duration=duration,
                    height=height,
                    width=width,
                    thumb=video_thumbnail,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "<b>Uploading Video as a Media...</b>",
                        editable,
                        c_time,
                    ),
                )
                download_link = dl.video.file_id

            elif merge_option == "streamtape":
                download_link = await streamtape_upload(
                    editable,
                    outfile_name,
                    file_size,
                    video_thumbnail,
                )

            await editable.delete()

    all_videos = users_files[chat_id]["vids"]
    vid_keys = list(all_videos.keys())
    file_ids = [
        all_videos[i]["video"]["file_id"] or all_videos[i]["document"]["file_id"]
        for i in vid_keys
    ]

    # usage is already counted in the function
    userdb.done_merging(download_link, file_name, file_size, file_ids, merge_option)

    await sleep(3)
    del users_files[chat_id]  # reset videos
    rmtree(f"{Vars.DOWN_PATH}/{chat_id}/")
    return
