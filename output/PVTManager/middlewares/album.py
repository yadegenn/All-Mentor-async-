import asyncio
from typing import Union

from telebot import SkipHandler
from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: Union[int, float] = 0.1) -> None:
        super().__init__()
        self.update_types = ['message']
        self.latency = latency
        self.album_data = {}

    def collect_album_messages(self, message):
        """
        Collect messages of the same media group.
        """
        #         # Check if media_group_id exists in album_data
        if message.media_group_id not in self.album_data:
            #             # Create a new entry for the media group
            self.album_data[message.media_group_id] = {"messages": []}
        #
        #         # Append the new message to the media group
        self.album_data[message.media_group_id]["messages"].append(message)
        #
        #         # Return the total number of messages in the current media group
        return len(self.album_data[message.media_group_id]["messages"])

    async def pre_process(self, message, data):
        if not message.media_group_id:
            return SkipHandler()
        total_before = self.collect_album_messages(message)
        await asyncio.sleep(self.latency)
        total_after = len(self.album_data[message.media_group_id]["messages"])
        if total_before != total_after:
            return CancelUpdate()
        album_messages = self.album_data[message.media_group_id]["messages"]
        album_messages.sort(key=lambda x: x.message_id)
        data["album"] = album_messages
        del self.album_data[message.media_group_id]
        return SkipHandler()

    async def post_process(self, message, data, exception):
        pass