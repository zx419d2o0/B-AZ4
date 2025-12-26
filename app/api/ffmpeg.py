from fastapi import APIRouter, Response, Request
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from functools import wraps
import urllib.parse
import subprocess
import asyncio
import hashlib
import shutil
import base64
import fcntl
import math
import io
import os
import av
import re

router = APIRouter()

@router.get("/extract-audio")
async def extract_audio(request: Request):
    url = str(request.query_params).split('url=')[-1]
    url = urllib.parse.unquote(url)
    if not re.search(r'(m3u8|mp4)', url, re.IGNORECASE):
        # response = await http_client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        # html = urllib.parse.unquote(response.text)
        # pattern = r"window\.__APOLLO_STATE__=(.*?)\s*;\(function\(\)"
        # matches = re.findall(pattern, html, re.DOTALL)
        # if not matches:
        # return html
        # json_data = json.loads(matches[0])
        # return json_data
        # url = json_data.get('defaultClient', {})
        # for key, val in url.items():
        #     if 'photoId' in key:
        #         print(val)
        return
    # 创建流容器
    container = av.open(url)

    # 查找音频流
    audio_stream = None
    for stream in container.streams:
        if stream.type == 'audio':
            audio_stream = stream
            break

    # 创建一个 BytesIO 对象来存储 MP3 数据
    mp3_output = io.BytesIO()

    # 打开输出容器，设置为 MP3 格式
    output_container = av.open(mp3_output, mode='w', format='mp3')
    
    # 创建一个音频流并为其指定 MP3 编码
    output_audio_stream = output_container.add_stream('mp3', rate=audio_stream.rate)

    # 解码并编码音频数据
    for packet in container.demux(audio_stream):
        for frame in packet.decode():
            # 转码并写入输出文件
            packet = output_audio_stream.encode(frame)
            output_container.mux(packet)
    
    # 关闭输出容器
    output_container.close()
    
    # 获取转换后的 MP3 数据
    mp3_output.seek(0)
    return StreamingResponse(mp3_output, media_type="audio/mpeg")

@router.post("/ff")
async def read_ff_info(request: Request):
    file_content = await request.body()  # 获取二进制数据
    if not file_content:
        return "Invalid file content"
    
    byte_data = io.BytesIO(file_content)
    # if url:
    #     response = session.get(url, headers={"User-Agent": "AptvPlayer/1.2.3"})
    #     data = io.BytesIO(response.content)
    try:
        container = av.open(byte_data)
    except Exception as e:
        print(e, byte_data)
        return "Invalid file content"

    result = {}
    for packet in container.demux(video=0):
        result['average_rate'] = packet.stream.average_rate.numerator
        result['codec_type'] = packet.stream.codec_context.type
        result['codec_name'] = packet.stream.codec_context.name
        break

    for index, frame in enumerate(container.decode(video=0)):
        result['url'] = container.name
        result['index'] = index
        result['width'] = frame.width
        result['height'] = frame.height

        buf = io.BytesIO()
        frame.to_image().save(buf, format="JPEG")
        result['image_data'] = base64.b64encode(buf.getvalue()).decode()
        break

    # return Response(content='data:image/jpeg;base64,' + result['data'], media_type='image/jpeg')
    return result
    
@router.post("/add")
async def read_ps_add(request: Request):
    form = await request.form()
    url = form.get('url')
    delay = int(form.get('delay', -1))
    name = form.get('name', '')
    # if len(request.url.query.split('url=')) < 2:
    #     return "Invalid URL"
    if not url.startswith('http') and (not url.endswith('.m3u') or not url.endswith('.m3u8')):
        return ''
    
    manager = ConversionManager()
    # dash_converter = manager.get_dash_converter(request.url.query.split('url=')[1])
    dash_converter = manager.get_dash_converter(url, name=name, delay=delay)
    
    return dash_converter.path

@router.post("/del")
async def read_ps_del(request: Request):
    form = await request.form()
    manager = ConversionManager()
    res = manager.remove_dash_converter(form.get('id'))
    return res

@router.post("/list")
async def read_ps_list():
    manager = ConversionManager()
    return manager.list_dash_converters()

@router.post("/start")
async def read_ps_start(request: Request):
    form = await request.form()
    manager = ConversionManager()
    res = manager.run_dash_converter(form.get('id'))
    return res

@router.post("/stop")
async def read_ps_stop(request: Request):
    form = await request.form()
    manager = ConversionManager()
    res = manager.stop_dash_converter(form.get('id'))
    return res

@router.post("/rss")
async def read_ps_rss():
    lines = []
    manager = ConversionManager()
    for item in manager.list_dash_converters():
        channel_genre = item.get('name') or item.get('id')
        channel_name = item.get('name') or item.get('origin_url')
        lines.append(channel_genre + ',#genre#')
        lines.append(channel_name + ',' + item.get('m3u8_url'))

    return Response('\n'.join(lines), media_type='application/x-mpegURL', headers={'Content-Disposition': 'attachment; filename="local.txt"'})
    # response = StreamingResponse(StringIO('\n'.join(lines)), media_type='application/x-mpegURL')
    # response.headers['Content-Disposition'] = 'attachment; filename="local.m3u8"'
    # return response

def singleton(cls):
    instances = {}

    @wraps(cls)  # 保留原有的函数签名和文档
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return wrapper

@singleton
class ConversionManager:
    def __init__(self):
        self.tasks = {}

    def get_dash_converter(self, input_file_url, name='', delay=-1):
        dash_converter = DASHConverter(input_file_url, desc=name, hls_time=delay)
        if dash_converter.task_id in self.tasks:
            return self.tasks[dash_converter.task_id]
        else:
            self.tasks[dash_converter.task_id] = dash_converter
            return dash_converter
        
    def run_dash_converter(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id].start_conversion()
            return True
        else:
            return False
        
    def stop_dash_converter(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id].stop_conversion()
            return True
        else:
            return False
        
    def remove_dash_converter(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id].stop_conversion()
            self.tasks[task_id].clear_resources()
            del self.tasks[task_id]
            return True
        else:
            return False
        
    def list_dash_converters(self):
        return [
            {
            'id': item.id,
            'name': item.desc,
            'm3u8_url': item.path,
            'status': item.isRunning,
            'length': item.length,
            'push_duration': item.duration,
            'target_duration': item.hls_time,
            'origin_url': item.input_file_url,
            'console': item.console_output
            } 
            for item in self.tasks.values()
        ]


class DASHConverter:
    def __init__(self, input_file_url:str, hls_time:int=30, name:str='', desc:str=''):
        self.input_file_url = input_file_url
        self.name = name or input_file_url
        if hls_time < 10 or hls_time > 60:
            hls_time = 30
        self.hls_time = hls_time
        self.desc = desc
        self.task_id = self.generate_task_id(input_file_url)
        self.filename = input_file_url.split('/')[-1].split('=')[-1]
        self.output_mpd = f'./cache/{self.task_id}/{self.filename}.mpd'
        self.output_m3u = f'./cache/{self.task_id}/{self.filename}.m3u8'
        self.process = None
        self.daemon_task = None
        self.daemon_task_running = False
        self.console_output = []
        self.last_exec_time = datetime.now()

    @property
    def id(self):
        return self.task_id

    @property
    def path(self):
        return "http://192.168.3.2:4191/dash/"  + self.task_id + "/" + self.filename + ".m3u8"
    
    @property
    def isRunning(self):
        if self.process and self.process.poll() is None:
            return True
        else:
            return False
        
    @property
    def length(self):
        count = 0.0
        try:
            with open(self.output_m3u, 'r') as f:
                for line in f.readlines():
                    if line.strip().startswith('#EXTINF:'):
                        count += float(line.split(':')[-1].split(',')[0])
        except Exception as e:
            # print('Error while counting files')
            pass
        return count
    
    @property
    def duration(self):
        if self.process and self.process.poll() is None:
            time_diff = datetime.now() - self.last_exec_time
            hours = time_diff.seconds // 3600
            minutes = (time_diff.seconds % 3600) // 60
            seconds = time_diff.seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return False

    def generate_task_id(self, input_file_url):
        # 使用 URL 的哈希值作为任务 ID
        url_hash = hashlib.md5(input_file_url.encode()).hexdigest()
        return url_hash[:8]  # 取前 8 位作为任务 ID

    def start_conversion(self):
        self.last_exec_time = datetime.now()
        if not self.process or self.process.poll() is not None:
            # command = [
            #     'ffmpeg',
            #     '-i', self.input_file_url,
            #     '-c:v', 'libx264',  # 使用 H.264 编码器
            #     '-preset', 'ultrafast',  # 使用超快预设以提高速度
            #     '-crf', '23',  # 设置恒定质量的调整因子（可根据质量需求调整，18-28之间，值越低质量越高）
            #     '-f', 'dash',
            #     '-window_size', '5',
            #     '-extra_window_size', '5',
            #     '-remove_at_exit', '1',
            #     '-live', '1',
            #     '-seg_duration', '4',
            #     self.output_mpd
            # ]
            command = [
                'ffmpeg',
                '-i', self.input_file_url,
                '-c:v', 'copy', # h264
                '-crf', '23',
                '-preset', 'fast', # ultrafast
                '-c:a', 'copy', # aac
                # '-b:a', '128k',
                '-hls_time', str(self.hls_time),
                '-hls_list_size', str(math.ceil(120/int(self.hls_time))),
                '-hls_flags', 'append_list+delete_segments',
                '-hls_delete_threshold', '1',
                self.output_m3u
            ]
            os.makedirs('./cache/'+self.task_id, exist_ok=True)
            self.console_output = []
            self.process = subprocess.Popen(command, stderr=subprocess.PIPE)
            self.start_daemon_task()
            return f"Conversion started for task ID: {self.task_id}"
        else:
            return "Conversion is already in progress"

    def stop_conversion(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            self.stop_daemon_task()
            return f"Conversion stopped for task ID: {self.task_id}"
        else:
            return "No active conversion to stop"
        
    async def daemon_task_conversion(self):
        self.daemon_task_running = True
        while self.daemon_task_running:
            # print(self.task_id, "Daemon task running...", self.last_exec_time.strftime("%Y-%m-%d %H:%M:%S"))
            await asyncio.sleep(60)

            if  datetime.now() - self.last_exec_time > timedelta(seconds=100):
                print(self.task_id, 'No request for 100 seconds, stopping conversion...', self.last_exec_time.strftime("%Y-%m-%d %H:%M:%S"))
                self.stop_conversion()
                continue

            output_reader = NonBlockingOutputReader(self.process)
            new_output = output_reader.read_output()
            self.console_output += new_output
            # for log in new_output:
            #     print(log)
            if len(new_output) == 0:
                print(self.task_id, "Command output is empty, restarting conversion...", len(self.console_output))
                self.stop_conversion()
                self.start_conversion()

    def start_daemon_task(self):
        if not self.daemon_task_running:
            self.daemon_task = asyncio.create_task(self.daemon_task_conversion())
            return f"Daemon task started for task ID: {self.task_id}"
        else:
            return "Daemon task is already running"
    
    def stop_daemon_task(self):
        if self.daemon_task_running:
            self.daemon_task_running = False
            self.daemon_task.cancel()
            return f"Daemon task stopped for task ID: {self.task_id}"
        else:
            return "Daemon task is not running"
        
    def clear_resources(self):
        try:
            shutil.rmtree('./cache/' + self.task_id)
        except Exception as e:
            print('path not exists', self.task_id, self.input_file_url)

class NonBlockingOutputReader:
    def __init__(self, process):
        self.process = process
        self.make_non_blocking(self.process.stderr.fileno())
        self.output = b''

    def make_non_blocking(self, fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def read_output(self):
        try:
            chunk = self.process.stderr.read()
            if chunk:
                self.output += chunk
                return self.output.decode('utf-8', 'ignore').splitlines()
            elif self.process.poll() is not None:
                # 进程结束且没有更多输出时返回空列表
                return []
            else:
                # 没有新输出时返回空列表
                return []
        except BlockingIOError:
            # 没有新输出时返回空列表
            return []