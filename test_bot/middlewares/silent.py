from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate

from ..utils.io import load_silent_user

silent_users = set()


class SilentMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        self.update_types = ['message', "message_reaction", "edited_message"]


    async def pre_process(self, message, data):
        silent_users = await load_silent_user()
        text = getattr(message, 'text', None) or ""
        if(message.chat.type=="supergroup" and not text.startswith("/") or message.chat.type=="group" and not text.startswith("/")):
            if(len(silent_users)>0):
                for i in silent_users:
                    if(i == message.message_thread_id):
                        return CancelUpdate()
            else:
                pass


    async def post_process(self, message, data, exception):
        pass