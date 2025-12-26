def register_handler(bot):
    @bot.message_handler(commands=['help'])
    async def help_handler(message):
        result = []
        commands = [x.get('filters').get('commands') for x in bot.message_handlers]
        for filter in commands:
            if filter:
                for command in filter:
                    result.append(command + ' - Description')
        await bot.reply_to(message, '\n'.join(result))