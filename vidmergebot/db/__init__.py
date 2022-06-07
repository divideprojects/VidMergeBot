from datetime import datetime
from typing import Any, Dict, List

from vidmergebot import LOGGER
from vidmergebot.db.mongo import MongoDB
from vidmergebot.vars import Vars


class MainDB(MongoDB):
    # TODO: change collection name to "users" or botname_users
    db_name = Vars.BOT_USERNAME

    def __init__(self, user_id: int) -> None:
        super().__init__(MainDB.db_name)
        self.user_id = user_id
        self.user_info = self.__ensure_in_db()

    def done_merging(
        self,
        merged_vid: str,
        file_name: str,
        file_size: int,
        vid_list: list,
        upload_option: str,
    ) -> None:
        """
        Updates the database with the merged video
        """
        self.user_info["merges"][merged_vid] = {
            "name": file_name,
            "size": file_size,
            "vids": vid_list,
            "upload": upload_option,
            "time": datetime.now(),
        }
        self.set_usage()
        self.update({"_id": self.user_id}, self.user_info)
        return

    def get_plan(self) -> str:
        """
        Get plan of user
        """
        return self.user_info.get("plan", "free")

    def set_usage(
        self,
        update_date=datetime.utcnow().date(),
        usage_value: int = 1,
    ) -> None:
        """
        Set usage of user
        """
        self.update(
            {"_id": self.user_id},
            {
                "usage": self.user_info.get("usage", {})
                | {str(update_date): self.get_usage() + usage_value},
            },
        )
        return

    def get_usage(self, date_today=datetime.utcnow().date()) -> int:
        """
        Get usage of user
        """
        return self.user_info.get("usage", {}).get(str(date_today), 0)

    @staticmethod
    def delete_user(user_id: int) -> None:
        """
        Delete user from database
        """
        return MongoDB(MainDB.db_name).delete_one({"_id": user_id})

    @staticmethod
    def get_all_users() -> List[int]:
        """
        Get all users in database
        """
        return [user["_id"] for user in MongoDB(MainDB.db_name).find_all()]

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """
        Get everything from collection
        """
        return MongoDB(MainDB.db_name).find_all()

    @staticmethod
    def total_users_count() -> int:
        """
        Get count of total users in database
        """
        return MongoDB(MainDB.db_name).count()

    def __ensure_in_db(self) -> Dict[str, Any]:
        user_data = self.find_one({"_id": self.user_id})
        if not user_data:
            new_data = {
                "_id": self.user_id,  # user id of user
                "plan": "free",  # plan of user
                "merges": {},  # All videos merged by user
                "join_date": datetime.now(),  # Joining date of user with time
                "usage": {},  # List of usage of user
            }
            self.insert_one(new_data)
            LOGGER.info(f"Initialized New User: {self.user_id}")
            return new_data
        return user_data
