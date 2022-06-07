from threading import RLock
from time import perf_counter, time

from cachetools import TTLCache
from pyrogram.types import CallbackQuery
from pyrogram.types.messages_and_media.message import Message

from vidmergebot import LOGGER
from vidmergebot.vars import Vars

THREAD_LOCK = RLock()

# users stay cached for 5 minutes
block_time = Vars.CACHE_TIME * 60
USER_CACHE = TTLCache(maxsize=512, ttl=block_time, timer=perf_counter)


async def user_cache_reload(m: Message or CallbackQuery):
    """
    Cache user in TTLCache for specified time
    """
    global USER_CACHE
    with THREAD_LOCK:
        user_id = m.from_user.id

        # Don't restrict owner
        if user_id == Vars.OWNER_ID:
            return

        USER_CACHE[user_id] = time() + block_time
        LOGGER.info(
            f"Restricting {user_id} for {block_time}s",
        )
        return


async def user_cache_check(m: Message or CallbackQuery):
    """
    Check cache status of user, return True if cached, else False
    along with time left for user to get un-cached
    """
    global USER_CACHE
    with THREAD_LOCK:
        user_id = m.from_user.id

        if user_id in USER_CACHE.keys():
            return True, USER_CACHE[user_id] - time()

        return False, 0
