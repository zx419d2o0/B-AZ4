import asyncio
import aiohttp
import base64
import math
import sys
import os

from datetime import datetime, timezone, timedelta
from core.config import config

class GIT:
    dict_save = {}

    def __init__(self):
        self.headers = { 'Authorization': 'Bearer ' + config.GITHUB_TOKEN }
        self.page_size = 30
        self.total_tasks = 0  # 总任务数
        self.completed_tasks = 0  # 已完成任务数
        self.failed_tasks = 0  # 已完成任务数
        self.lock = asyncio.Lock()  # 用于保护任务计数的锁

    async def search_code(self, q, page=1, pattern='.*', days=30):
        """ 异步搜索代码 """
        params = {
            'q': q,
            'page': page,
            'per_page': 100
        }

        if q == self.dict_save.get('query') and len(self.dict_save.get('list_files'))/100 >= page:
            return self.dict_save

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com/search/code", params=params, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        json_data = await response.json()

                        if q != self.dict_save.get('query'):
                            self.dict_save = {
                                'query': q,
                                'days': days,
                                'list_files': json_data.get('items'),
                                'total_count': json_data.get('total_count'),
                                'page_count': min(math.ceil(json_data.get('total_count') / 30), 30),
                                'list_filtered': list(),
                                'pages': dict(),
                                'recorded': set()
                            }
                        else:
                            self.dict_save['list_files'].extend(json_data.get('items', []))
                        return self.dict_save
                    else:
                        print(f"Failed to fetch data: {response.status}")
                        return None
        except:
            print('search_code error')
    
    async def get_commit(self, session, repo_full_name, file_path, branch='main'):
        """ 使用 aiohttp 获取文件的提交信息 """
        url = f"https://api.github.com/repos/{repo_full_name}/commits"
        params = {
            'path': file_path,
            'sha': branch,
        }
        try:
            async with session.get(url, params=params, headers=self.headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:  # 确保有提交信息
                        return data[0]  # 返回最近一次提交的信息
                return None
        except:
            print('get_commit error')
        
    async def get_file_content(self, session, file_url):
        """ 获取文件内容并解码 """
        try:
            async with session.get(file_url, headers=self.headers, timeout=5) as response:
                if response.status == 200:
                    json_data = await response.json()
                    content = base64.b64decode(json_data.get('content')).decode('utf-8')
                    return content
                else:
                    print(f"Failed to fetch {file_url}, status code: {response.status}")
                    return ''
        except Exception as e:
            print(f"Error fetching file content: {e}")
            return ''
        
    async def _check_filter_conditions(self, file):
        """ 检查文件是否符合筛选条件 """
        last_modified_datetime = datetime.strptime(file.get('last_modified_datetime'), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        if file.get('owner') in self.dict_save['recorded']:
            return False
        if file.get('match_text') in self.dict_save['recorded']:
            return False
        if current_time - last_modified_datetime > timedelta(days=self.dict_save.get('days')):
            return False
        return True

    async def get_contentfile_info(self, session, contentfile, page):
        """ 异步获取文件详细信息并存储 """
        # 获取 repository 信息
        repo_full_name = contentfile.get("repository", {}).get("full_name", "")
        file_path = contentfile.get("path", "")
        branch = contentfile.get("url").split('ref=')[-1]

        # 获取提交信息
        commit = await self.get_commit(session, repo_full_name, file_path, branch)
        if not commit:
            await self._update_task_count(False)
            return
        
        content = await self.get_file_content(session, contentfile.get('url'))
        
        result = {
            'path': contentfile.get('path'),
            'html_url': contentfile.get('html_url'),
            'download_url': contentfile.get('url'),
            'owner': contentfile.get('repository', {}).get('owner', {}).get('login'),
            'last_modified_datetime': commit.get('commit', {}).get('committer', {}).get('date'),
            'content': content
        }

        for line in content.split('\n'):
            if self.dict_save.get('query') in line:
                result['match_text'] = line.strip()
                break

        # 在处理结果时检查是否符合筛选条件
        if await self._check_filter_conditions(result):
            self.dict_save['list_filtered'].append(result)
            self.dict_save['recorded'].add(result.get('match_text'))
            self.dict_save['recorded'].add(result.get('owner'))

        self.dict_save['pages'].setdefault(page, []).append(result)
        await self._update_task_count(True)

    async def get_page_data(self, page=1):
        """ 获取页面数据 """
        # 检查缓存中是否已有数据
        if page in self.dict_save['pages']:
            return self.dict_save['pages'][page]
        
        # 如果当前页数据不足且总数据还未请求完
        if len(self.dict_save['list_files']) < page * self.page_size and page * self.page_size <= self.dict_save['total_count']:
            await self.search_code(self.dict_save['query'], page=len(self.dict_save['list_files'])/100 + 1)

        # 如果没有缓存，异步查询数据
        files = self.dict_save['list_files'][(page - 1) * self.page_size: page * self.page_size]

        # 更新任务总数
        self.total_tasks = len(files)
        self.completed_tasks = 0
        self.failed_tasks = 0

        async with aiohttp.ClientSession() as session:
            tasks = [self.get_contentfile_info(session, file, page) for file in files]
            await asyncio.gather(*tasks)

        self._wrtie_line(f'total: {self.total_tasks}, completed: {self.completed_tasks}, failed: {self.failed_tasks}, filtered: {len(self.dict_save["list_filtered"])}')
        # 返回该页的数据并缓存
        # return self.dict_save['pages'][page]
    
    async def get_filtered_data(self, page_num=1, count=10, callback=None):
        """ 获取筛选后的数据 """
        # 根据页数计算起始索引和结束索引
        start_index = (page_num - 1) * count  # 当前页的起始索引
        end_index = start_index + count  # 当前页的结束索引

        # 如果当前符合条件的数据已经足够，直接返回
        if len(self.dict_save['list_filtered']) >= end_index:
            return self.dict_save['list_filtered'][start_index:end_index]
        
        max_requests = 10  # 最大请求次数
        request_count = 0  # 当前请求次数
        # 如果list_filtered中的数据不够，继续请求更多的数据
        while len(self.dict_save['list_filtered']) < end_index:
            # 获取最大page索引并判断是否还可以继续请求
            last_page = max(self.dict_save['pages'].keys(), default=0)
            # 如果达到最大请求次数，停止请求并更新page_count
            if request_count >= max_requests:
                break

            # 如果当前已请求的数据小于total_count，则继续请求新页面
            if last_page == 0 or last_page * self.page_size < self.dict_save.get('total_count'):
                if (callback):
                    await callback({
                        'current': len(self.dict_save['list_filtered']),
                        'need': end_index,
                        'page': last_page + 1,
                        'page_count': self.dict_save['page_count']
                    })
                await self.get_page_data(last_page + 1)
                request_count += 1  # 增加请求计数器
            else:
                # 如果没有更多的数据页了，停止请求
                break

        # 返回满足筛选条件的前 `count` 条数据
        return self.dict_save['list_filtered'][start_index:end_index]
    
    async def _update_task_count(self, success):
        async with self.lock:
            if success:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1
        self._update_progress(self.completed_tasks + self.failed_tasks, self.total_tasks)
    
    def _update_progress(self, current, total):
        progress = int((current / total) * 100)
        # 更新进度条
        progress_bar = f"\r[{'=' * (progress // 2)}{' ' * (50 - progress // 2)}] {progress}%"
        sys.stdout.write(progress_bar)
        sys.stdout.flush()

    def _wrtie_line(self, content):
        # 插入新行并打印内容
        sys.stdout.write("\033[1L")
        sys.stdout.write(f"{content}\n")
        sys.stdout.flush()

git = GIT()


if __name__ == '__main__':
    git = GIT()
    asyncio.run(git.search_code('live?url=https://www.youtube.com/', days=720, pattern=r'.+(?=https://www\.youtube\.com/)'))
    result = asyncio.run(git.get_filtered_data())
    print(result)
