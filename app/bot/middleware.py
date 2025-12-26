from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate

class Middleware(BaseMiddleware):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.update_types = ['message']
        # Always specify update types, otherwise middlewares won't work


    async def pre_process(self, message, data):
        if message.from_user.id == 6645610577:
            pass
        else:
            await self.bot.send_message(message.chat.id, 'You are not authorized to use this bot')
            return CancelUpdate()
        # if not message.from_user.id in self.last_time:
        #     # User is not in a dict, so lets add and cancel this function
        #     self.last_time[message.from_user.id] = message.date
        #     return
        # if message.date - self.last_time[message.from_user.id] < self.limit:
        #     # User is flooding
        #     await self.bot.send_message(message.chat.id, 'You are making request too often')
        #     return CancelUpdate()
        # self.last_time[message.from_user.id] = message.date

        
    async def post_process(self, message, data, exception):
        if exception:
            print(f'[{message.text}]: {exception}')
