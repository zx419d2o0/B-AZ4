from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re

def create_page_buttons(page_length: int, page_count: int = 5, page_num: int = 0) -> InlineKeyboardMarkup:
    # 创建分页按钮
    ikm = InlineKeyboardMarkup(row_width=page_count)

    # 总页数小于等于5，直接返回中间所有页码
    if page_length - 2 <= page_count:
        start_page = 1
        end_page = page_length - 2
    else:
        # 常规情况下计算页码范围
        start_page = max(1, page_num - 2)
        end_page = min(page_length - 2, page_num + 2)

        # 调整范围以确保显示 page_count 个页码
        if end_page - start_page + 1 < page_count:
            if start_page == 1:
                end_page = min(page_length - 2, start_page + page_count - 1)
            else:
                start_page = max(1, end_page - page_count + 1)

    first_button = InlineKeyboardButton("*1*" if 0 == page_num else "1" , callback_data=f"prev_0" if 0 != page_num else "null")
    # 上一页按钮
    prev_button = InlineKeyboardButton("<", callback_data=f"prev_{page_num-1}") if page_num > 0 else None
    
    # 页码按钮
    page_buttons = [
        InlineKeyboardButton(
            f"*{i+1}*" if i == page_num else str(i+1),
            callback_data=f"page_{i}" if i != page_num else "null"
        )
        for i in range(start_page, end_page + 1)
    ]
    
    last_button = InlineKeyboardButton(f'*{page_length}*' if page_length - 1 == page_num else str(page_length), callback_data=f"next_{page_length-1}" if page_length - 1 != page_num else "null")
    # 下一页按钮
    next_button = InlineKeyboardButton(">", callback_data=f"next_{page_num+1}") if page_num < page_length - 1 else None

    buttons = []
    buttons.append(first_button)
    # if prev_button:
    #     buttons.append(prev_button)
    buttons.extend(page_buttons)
    # if next_button:
    #     buttons.append(next_button)
    if page_length > 1:
        buttons.append(last_button)
    ikm.row(*buttons)

    return ikm

def create_progress_bar(current_progress: int, total_progress: int) -> str:
    """根据当前进度和总进度生成进度条"""
    if total_progress <= 0:
        raise ValueError("Total progress must be greater than zero")
    if current_progress < 0:
        raise ValueError("Current progress cannot be negative")
    if current_progress > total_progress:
        raise ValueError("Current progress cannot exceed total progress")

    # 计算百分比
    percentage = int((current_progress / total_progress) * 100)

    # 定义进度条长度和字符
    bar_length = 40
    full_block = "█"
    empty_block = "░"
    
    # 计算进度条中的已完成和未完成部分
    progress_length = int((current_progress / total_progress) * bar_length)
    bar = full_block * progress_length + empty_block * (bar_length - progress_length)
    
    # 创建进度条字符串
    return f"[{bar}] {percentage}% ({current_progress}/{total_progress})"

def split_markdown(text: str, max_bytes: int=4096) -> list:
    """按最大字节数分割 Markdown 文本并确保标签闭合"""
    tag_pattern = re.compile(r'(\*\*|\_\_|[\*\_]{1,2}|```|~~~|`{1})')

    def extract_tags_and_positions(text):
        """提取所有标签及其位置"""
        tags = []
        for match in tag_pattern.finditer(text):
            tags.append((match.group(0), match.start()))
        return tags

    def find_last_valid_position(text, tags):
        """检查标签闭合状态，返回最后一个闭合的位置"""
        stack = []
        last_valid_pos = 0
        for tag, pos in tags:
            if tag in ("**", "__", "*", "_", "```", "~~~", "`"):
                if stack and stack[-1] == tag:  # 闭合标签
                    stack.pop()
                else:
                    stack.append(tag)  # 开始标签，入栈
            if not stack:  # 栈为空时，记录最后的闭合位置
                last_valid_pos = pos + len(tag)
        return last_valid_pos

    text = text.replace("*", "")
    # 如果文本长度小于等于 max_bytes，直接返回整个文本
    if len(text) <= max_bytes:
        return [text]

    # 对于大于 max_bytes 的文本，逐段检查和处理
    result = []
    remaining_text = text

    while remaining_text:
        # 截取 max_bytes 字节
        chunk = remaining_text[:max_bytes]
        tags = extract_tags_and_positions(chunk)  # 提取标签
        last_valid_pos = find_last_valid_position(chunk, tags)  # 找到最后闭合位置

        if last_valid_pos > 0:
            # 保存闭合部分
            result.append(chunk[:last_valid_pos])
            # 未闭合部分继续下一轮
            remaining_text = remaining_text[last_valid_pos:]
        else:
            # 当前段落没有标签未闭合，直接保存并退出
            result.append(chunk)
            remaining_text = remaining_text[max_bytes:]

    return result
