from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from telebot.async_telebot import AsyncTeleBot
    from telebot.types import Message, CallbackQuery
from services.git import git
from core.string_helper import create_page_buttons, create_progress_bar
import html


cmd_gitserach = 'gitsearch'
def register_handler(bot: 'AsyncTeleBot'):
    @bot.message_handler(commands=[cmd_gitserach])
    async def git_search_code(message: 'Message'):
        text = message.text[len(cmd_gitserach)+2:].split(',')
        q, days, max_count = (text + [''] * 3)[:3]  # 解构赋值，并用空字符串填充不足的部分
        q = q.strip()
        days = int(days.strip()) if days.strip().isdigit() else 30
        max_count = int(max_count.strip()) if max_count.strip().isdigit() else 30
        if not q:
            return

        dict_result = await git.search_code(q, days=days)
        if dict_result:
            msg = await bot.send_message(message.chat.id, f"search:{q}, days:{days}, total:{dict_result.get('total_count')}")
            await send_page(message.chat.id, 0, msg.message_id, msg.text)
        else:
            await bot.send_message(message.chat.id, 'error')

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('prev_', 'next_', 'page_')))
    async def callback_query(call: 'CallbackQuery'):
        page_num = int(call.data.split('_')[1])
        # global save_gitserach
        # if save_gitserach:
        await send_page(call.message.chat.id, page_num, call.message.message_id, keep_text=call.message.text)
        # else:
            # await bot.reply_to(call.message, 'no')

    async def send_page(chat_id, page_num, message_id=None, keep_text=''):
        async def handle_task(task):
            try:
                await on_task_get_info_done(task, chat_id, message_id, keep_text)
            #     result = await task  # 等待任务完成
            #     # 处理任务完成后的回调
            #     await on_task_get_info_done(result, length, chat_id, message_id, keep_text)
            except Exception as e:
                print(f"Task failed with exception: {e}")

        page_num += 1
        datas = await git.get_filtered_data(page_num, callback=handle_task)
        # datas = git.dict_save.get('pages', {}).get(page_num)
        # if not datas:
            # global counter
            # async with counter_lock:
            #     counter = 0
            # page_files = git.dict_save['list_files'].get_page(page_num)
            # tasks = {index : asyncio.create_task(git.get_contentfile_info(file, page_num)) for index, file in enumerate(page_files)}
            # for task in asyncio.as_completed(tasks.values()):
            #     await handle_task(task, len(page_files))
            # await git.get_page_data(page_num)
            # datas = git.dict_save.get('pages', {}).get(page_num)

        content = []
        # recorded = []
        for data in datas:
        #     if data.get('owner') in recorded:
        #         continue
        #     if data.get('match_text') in recorded:
        #         continue
        #     last_modified_datetime = datetime.strptime(data.get('last_modified_datetime') , "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        #     current_time = datetime.now(timezone.utc)
        #     if current_time - last_modified_datetime > timedelta(days=git.dict_save.get('days')):
        #         continue

        #     recorded.append(data.get('owner'))
        #     recorded.append(data.get('match_text'))
            html_url = data.get('html_url', '#')  # 默认值为 '#' 防止 KeyError
            path = data.get('path', 'Unknown')
            last_modified = data.get('last_modified_datetime', 'N/A')

            content.append(f"<a href='{html_url}'>{path}</a>\t,\t<b>{last_modified}</b>")
            content.append(f"{html.escape(data.get('match_text', 'file name:' + path))}")
            content.append('')
        
        content.append(f"page: {page_num} total: {len(git.dict_save.get('list_filtered'))}")
        text = '\n'.join(content) if content else '0'
        markup = create_page_buttons(git.dict_save.get('page_count'), page_num=page_num - 1)
        await bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=markup)
            
    async def on_task_get_info_done(task: dict, chat_id, message_id, keep_text=''):
        progress_bar = create_progress_bar(task.get('current'), task.get('need'))
        show_text = keep_text
        show_text += f"\tsearch: {task.get('page_count')}/{task.get('page', '')}"
        show_text += '\n' + progress_bar
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=show_text)
