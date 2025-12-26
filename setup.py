import os
from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext

# 定义目录路径
c_output_dir = os.path.join('build', 'c')  # .c 文件的输出目录
so_output_dir = 'dist'  # .so 文件的输出目录

# 确保目标目录存在
os.makedirs(c_output_dir, exist_ok=True)
os.makedirs(so_output_dir, exist_ok=True)
# file_structure = {}

# 遍历目录及文件
# for dirpath, dirnames, filenames in os.walk(source_dir):
#     for filename in filenames:
#         # 过滤出 .py 文件
#         if filename.endswith('.py'):
#             # 获取无扩展名的文件名
#             file_name_without_ext = os.path.splitext(filename)[0]
#             # 相对路径（相对于 source_dir）
#             relative_dir = os.path.relpath(dirpath, source_dir)
#             # 创建 key，格式：目录.文件名（无扩展名）
#             if relative_dir == '.':
#                 key = file_name_without_ext
#             else:
#                 key = f"{relative_dir.replace(os.sep, '.')}.{file_name_without_ext}"
#             # 保存相对路径（只保留从 source_dir 开始的部分）
#             file_structure[key] = so_output_dir + os.sep +  relative_dir  # 只保留相对目录

# 自定义 build_ext 类，确保 .so 文件按原目录结构存储
class CustomBuildExt(build_ext):
    def build_extensions(self):
        # 保证 build_lib 指向目标 .so 文件目录
        self.build_lib = so_output_dir
        super().build_extensions()

    # 匹配函数，按从后向前的顺序匹配 key
    # def get_map_dir(self, target_key):
    #     # 将目标 key 按 '.' 分割成各个部分
    #     target_parts = target_key.split('.')
        
    #     # 遍历字典中的键值对
    #     for key, value in file_structure.items():
    #         # 将字典中的 key 按 '.' 分割成各个部分
    #         key_parts = key.split('.')
            
    #         # 从后往前匹配 key 的部分
    #         if key_parts[-len(target_parts):] == target_parts:
    #             return value  # 如果匹配成功，返回整个 value
        
    #     return None  # 如果没有匹配到，返回 None

    def get_ext_fullpath(self, ext_name):
        """
        返回扩展模块的完整路径，确保按原目录结构存储
        """
        # 获取编译后文件的扩展名
        ext_suffix = self.get_ext_filename(ext_name).split(ext_name.replace(".", os.sep))[-1]
        
        # 计算源文件的相对路径
        source_relative_path = ext_name.replace(".", os.sep) + ext_suffix
        # full_path = os.path.join(self.get_map_dir(ext_name), source_relative_path)
        full_path = os.path.join(self.build_lib, source_relative_path)
        
        # 确保目录结构存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

# 执行 cythonize，生成 .c 文件，并将其保存在指定目录
extensions = cythonize(
    os.path.join('app', "**/*.py"),  # 编译的所有 Python 文件
    compiler_directives={'language_level': "3"},
    build_dir=c_output_dir  # 存放 .c 文件的目录
)

# 使用 setuptools 配置安装
setup(
    name="cython_extension",
    ext_modules=extensions,
    cmdclass={"build_ext": CustomBuildExt},
    options={
        "build_ext": {
            "build_lib": so_output_dir,  # .so 文件存放的目标目录
        }
    }
)