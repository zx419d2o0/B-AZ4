import os
from pathlib import Path


class FileHelper:
    def __init__(self):
        self.base_dir = self._detect_output_dir()

    @staticmethod
    def _detect_output_dir():
        if os.uname().sysname == 'Linux':
            return Path('/home/data')

        return Path.cwd() / 'output'

    def save_file(self, name: str, content: bytes) -> str:
        file_path = self.base_dir / name

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_bytes(content)

        return str(file_path)
    
file_manager = FileHelper()