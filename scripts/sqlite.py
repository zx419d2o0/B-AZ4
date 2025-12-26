from utils.common import singleton, deprecated
from utils.log import logger
from collections import namedtuple
from datetime import datetime
import pandas as pd
import sqlite3
import pathlib


class FieldProps:
    """
    表示字段的属性，用于描述字段在表中的特性，如主键、可空性、默认值、唯一性等
    """
    def __init__(self, is_primary_key=False, is_nullable=True, default=None, is_unique=False, is_autoincrement=False):
        """
        初始化字段属性
        
        :param is_primary_key: 是否为主键，默认为 False
        :param is_nullable: 是否允许为空，默认为 True
        :param default: 默认值，默认为 None
        :param is_unique: 是否唯一，默认为 False
        :param is_autoincrement: 是否自增，默认为 False
        """
        self.is_primary_key = is_primary_key
        self.is_nullable = is_nullable
        self.default = default
        self.is_unique = is_unique
        self.is_autoincrement = is_autoincrement


class Table:
    """基础表类，用于定义表的基本操作"""
    table_name = "unknown"
    
    def __init__(self, db_instance):
        """
        初始化表类对象
        
        :param db_instance: Database 实例
        """
        self.db: Database = db_instance  # 绑定数据库实例
        self.table_name = self.__class__.table_name  # 表名

    def _map_row_to_object(self, row: sqlite3.Row):
        """
        将查询结果行映射为表类的对象
        
        :param row: 查询结果的一行
        :return: 返回一个表类的实例，字段值被动态设置
        """
        # 直接使用类的属性，动态设置字段值
        obj = self.__class__(self.db)  # 只传入 db 实例，不传字段值
        for column in row.keys():
            setattr(obj, column, row[column])  # 动态设置字段值
        return obj
    
    def _create_namedtuple_class(self, fields):
        """
        动态创建一个 namedtuple 类并重写 __hash__ 和 __eq__ 方法。

        :param fields: 字段列表，定义了 namedtuple 的属性。
        :return: 动态生成的 namedtuple 类。
        """
        # 动态创建 namedtuple 类
        Record = namedtuple("Record", fields)

        # 给这个类增加 __hash__ 和 __eq__ 方法
        class CustomRecord(Record):
            def __hash__(self):
                # 自定义哈希函数
                return hash(tuple(getattr(self, field) for field in fields))

            def __eq__(self, other):
                # 自定义相等比较函数
                if isinstance(other, CustomRecord):
                    return tuple(getattr(self, field) for field in fields) == tuple(getattr(other, field) for field in fields)
                return False

        return CustomRecord
    
    @staticmethod
    def get_sql_type(python_type):
        """
        根据 Python 类型返回对应的 SQL 数据类型
        
        :param python_type: Python 数据类型
        :return: 对应的 SQL 数据类型
        """
        if python_type == str:
            return 'TEXT'
        elif python_type == int:
            return 'INTEGER'
        elif python_type == float:
            return 'REAL'
        elif python_type == bool:
            return 'INTEGER'  # 以 0 和 1 存储布尔值
        elif python_type == datetime:
            return 'TEXT'  # 使用 ISO 8601 格式存储日期和时间
        else:
            raise TypeError(f"Unsupported type: {python_type}")

    @classmethod
    def generate_create_table_sql(cls):
        """
        生成创建表的 SQL 语句，根据类中的字段注解和字段属性
        
        :return: 创建表的 SQL 语句
        """
        sql_columns = []
        
        # 获取字段属性字典
        field_props_class = getattr(cls, "_field_props", {})
        
        # 遍历所有字段，生成列的 SQL 定义
        for column, field_props in field_props_class.items():
            col_type = cls.__annotations__.get(column)  # 获取字段的类型注解
            
            if col_type:  # 如果字段在类中有类型注解
                # 根据字段类型生成 SQL 列定义
                column_definition = f'"{column}" {cls.get_sql_type(col_type)}'
                
                # 添加字段属性：主键、默认值、是否可空、是否唯一
                if field_props.is_primary_key:
                    column_definition += ' PRIMARY KEY'
                if not field_props.is_nullable:
                    column_definition += ' NOT NULL'
                if field_props.default:
                    column_definition += f' DEFAULT {field_props.default}'
                if field_props.is_unique:
                    column_definition += ' UNIQUE'
                if field_props.is_autoincrement:
                    column_definition += ' AUTOINCREMENT'
                
                sql_columns.append(column_definition)
        
        columns_sql = ', '.join(sql_columns)
        create_table_sql = f'CREATE TABLE IF NOT EXISTS "{cls.table_name}" ({columns_sql});'
        return create_table_sql
    
    def select(self, format="table", select_fields=None, where_condition=None, join_table=None, join_type="INNER", on_condition=None):
        """
        查询数据，根据条件返回符合条件的数据
        
        :param fields: 选择的字段列表，默认为 None，表示选择所有字段
        :param join_table: 连接的其他表
        :param on_condition: 连接条件
        :param where_condition: 查询条件
        :return: 查询结果的表类对象列表
        """
        # 如果没有指定字段，则选择所有字段（*）
        if not select_fields:
            select_fields = ['*']  # 默认选择所有字段
        
        # 将字段列表转换成字符串，例如 ['id', 'name'] -> 'id, name'
        fields_str = ', '.join(select_fields)

        query = f"SELECT {fields_str} FROM {self.table_name}"
        
        # 处理连接表
        if join_table and on_condition:
            # 加入连接类型（'INNER', 'LEFT', 'RIGHT'）
            query += f" {join_type} JOIN {join_table} ON {on_condition}"
        
        # 处理 WHERE 条件
        if where_condition:
            query += f" WHERE {where_condition}"
        
        # print("sql:", query)
        with self.db.connect() as conn:
            conn.row_factory = sqlite3.Row  # 让查询结果支持字典式访问
            result = conn.execute(query).fetchall()
            if format == "table":
                return [self._map_row_to_object(row) for row in result]
            else:
                return [dict(row) for row in result]

    def insert_or_replace(self, data):
        """
        插入数据或替换已存在的记录，支持单条或多条数据。

        :param data_list: 单条或多条数据（字典或字典列表）
        """
        if isinstance(data, dict):  # 单条数据转为列表
            data = [data]

        if not data:
            raise ValueError("data_list cannot be empty.")

        # 提取字段和占位符
        keys = data[0].keys()
        columns = ', '.join(keys)
        placeholders = ', '.join(f":{key}" for key in keys)

        insert = f"INSERT OR REPLACE INTO {self.table_name} ({columns}) VALUES ({placeholders})"

        with self.db.connect() as conn:
            conn.executemany(insert, data)  # 字典格式直接绑定
            conn.commit()

    def update(self, condition, update_data: dict):
        """
        更新数据并同步到数据库
        
        :param condition: 更新的条件
        :param update_data: 更新的数据，字典形式
        """
        set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {condition}"
        with self.db.connect() as conn:
            conn.execute(query, tuple(update_data.values()))
            conn.commit()

    def delete(self, condition):
        """
        删除符合条件的数据
        
        :param condition: 删除条件
        """
        query = f"DELETE FROM {self.table_name} WHERE {condition}"
        with self.db.connect() as conn:
            conn.execute(query)
            conn.commit()

    def load_data_from_db(self):
        """
        从数据库加载表数据并返回 DataFrame
        
        :return: 加载的表数据
        """
        with self.db.connect() as conn:
            return pd.read_sql(f"SELECT * FROM {self.table_name}", conn)  # 使用 pandas 从数据库加载表数据

    @deprecated
    def append(self, data):
        """
        插入数据到表中，并更新 DataFrame
        
        :param data: 插入的数据，字典形式
        """
        data_df = pd.DataFrame([data])  # 将传入的数据转换为 DataFrame
        self.df = pd.concat([self.df, data_df], ignore_index=True)  # 将数据插入 DataFrame
        with self.db.connect() as conn:
            data_df.to_sql(self.table_name, conn, if_exists='append', index=False)  # 插入数据库

    @deprecated
    def query(self, condition=None):
        """
        查询数据，根据条件返回符合条件的数据
        
        :param condition: 查询条件，默认为 None
        :return: 查询结果
        """
        if condition:
            return self.df.query(condition)  # 使用 pandas 查询数据
        return self.df  # 如果没有条件，返回所有数据

    @deprecated
    def replace(self, condition, update_data: dict):
        """
        更新数据并同步到数据库，通过 SQL UPDATE 语句来更新数据库中的数据
        
        :param condition: 更新的条件
        :param update_data: 更新的数据，字典形式
        """
        # 使用 pandas 更新 DataFrame 中的数据
        for column, value in update_data.items():
            # 查找符合条件的行并更新对应的列
            self.df.loc[self.df.eval(condition), column] = value
        
        # 同步更新到数据库
        with self.db.connect() as conn:
            # 使用 pandas 将 DataFrame 更新回数据库
            self.df.to_sql(self.table_name, conn, if_exists='replace', index=False)  # 'replace' 会替换整个表
            
    @deprecated
    def remove(self, condition):
        """
        删除符合条件的数据
        
        :param condition: 删除条件
        """
        self.df = self.df[~self.df.eval(condition)]  # 使用 pandas 删除符合条件的行
        with self.db.connect() as conn:
            self.df.to_sql(self.table_name, conn, if_exists='replace', index=False)  # 删除数据库中的数据

    def query_merge(self, condition=None, join_table=None, left_on=None, right_on=None, how='inner'):
        """
        查询数据，根据条件返回符合条件的数据，并支持 JOIN 查询
        
        :param condition: 查询条件（可选），默认为 None
        :param join_table: 需要 JOIN 的表（可选）
        :param left_on: 主表连接的列（可选）
        :param right_on: 连接表连接的列（可选）
        :param how: 连接类型（'left', 'right', 'outer', 'inner'），默认是 'inner'
        :return: 查询结果，可能包括 JOIN 结果
        """
        # 加载数据
        df = self.load_data_from_db()
        if join_table is not None and left_on is not None and right_on is not None:
            # 执行 JOIN 查询
            result_df = pd.merge(df, join_table, left_on=left_on, right_on=right_on, how=how, suffixes=('_x', '_y'))

            # 手动为所有字段添加后缀
            for col in result_df.columns:
                # 检查是否已经有后缀，如果没有，则给该列添加后缀
                if not any(col.endswith(suffix) for suffix in ['_x', '_y']):
                    if col in df.columns:
                        result_df.rename(columns={col: col + '_x'}, inplace=True)
                    else:
                        result_df.rename(columns={col: col + '_y'}, inplace=True)

            # 处理字段，分配后缀
            x_columns = [col for col in result_df.columns if col.endswith('_x')]
            y_columns = [col for col in result_df.columns if col.endswith('_y')]

            # 提取去掉后缀 '_y' 的字段名
            y_fields = [col[:-2] for col in y_columns]

            # 定义 namedtuple
            Record = self._create_namedtuple_class(y_fields)

            # 遍历每一行，将 y_columns 中的字段值存入字典
            result_df["join_data"] = result_df.apply(
                lambda row: Record(**{field: row[col] for field, col in zip(y_fields, y_columns)}),
                axis=1
            )

            # 还原 x 表的字段名（去掉 '_x' 后缀）
            result_df.rename(columns={col: col[:-2] for col in x_columns}, inplace=True)

            # 删除 '_y' 后缀的列
            result_df = result_df.drop(columns=y_columns)
        else:
            result_df = df  # 如果没有 join，返回原始数据

        # 如果有条件，使用 pandas query 进行筛选
        if condition:
            return result_df.query(condition)  # 使用 pandas 查询数据

        return result_df
    

class TableAlbums(Table):
    """tab_albums 表类，自动根据字段和字段属性生成表的创建 SQL 语句"""
    table_name: str = 'tab_albums'
    id: str
    album: str
    artist: str
    url: str
    cover: str
    desc: str
    quality: str
    update_time: datetime

    # 字段属性
    _field_props = {
        'id': FieldProps(is_primary_key=True, is_nullable=False),
        'album': FieldProps(is_nullable=False),
        'artist': FieldProps(is_nullable=False),
        'url': FieldProps(is_nullable=False),
        'cover': FieldProps(is_nullable=False),
        'desc': FieldProps(is_nullable=False),
        'quality': FieldProps(is_nullable=False),
        'update_time': FieldProps(default='CURRENT_TIMESTAMP', is_nullable=False)
    }


class TableRecord(Table):
    """tab_record 表类，自动根据字段和字段属性生成表的创建 SQL 语句"""
    table_name: str = 'tab_record'
    id: str
    url: str
    desc: str
    interpreter: str
    search_date: datetime

    # 字段属性
    _field_props = {
        'id': FieldProps(is_primary_key=True, is_nullable=False),
        'url': FieldProps(is_nullable=False),
        'desc': FieldProps(is_nullable=False),
        'interpreter': FieldProps(is_nullable=False),
        'search_date': FieldProps(default='CURRENT_TIMESTAMP', is_nullable=False)
    }


class TableSongs(Table):
    """tab_songs 表类，自动根据字段和字段属性生成表的创建 SQL 语句"""
    table_name: str = 'tab_songs'
    id: str
    album_id: str
    no: str
    name: str
    url: str
    update_time: datetime

    # 字段属性
    _field_props = {
        'id': FieldProps(is_primary_key=True, is_nullable=False),
        'album_id': FieldProps(is_nullable=False),
        'no': FieldProps(is_nullable=False),
        'name': FieldProps(is_nullable=False),
        'url': FieldProps(is_nullable=False),
        'update_time': FieldProps(default='CURRENT_TIMESTAMP', is_nullable=False)
    }


class TableUserConfig(Table):
    """tab_songs 表类，自动根据字段和字段属性生成表的创建 SQL 语句"""
    table_name: str = 'tab_user_config'
    key: str
    value: str
    desc: str

    # 字段属性
    _field_props = {
        'key': FieldProps(is_primary_key=True, is_nullable=False),
        'value': FieldProps(),
        'desc': FieldProps()
    }


@singleton
class Database:
    """
    数据库管理类，负责管理所有表的创建和操作
    """
    # 在这里预先定义所有表的名称
    tab_albums: TableAlbums
    tab_record: TableRecord
    tab_songs: TableSongs
    tab_user_config: TableUserConfig

    def __init__(self):
        """初始化数据库对象"""
        self.db_path = pathlib.Path(__file__).parent.joinpath("../assets/sqlite.db")  # 数据库文件路径
        
        # 初始化所有表
        self.initialize()

    def connect(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)  # 返回 SQLite 连接对象

    def initialize(self):
        """
        初始化数据库，加载所有定义的表
        
        遍历所有表类，根据字段属性生成表并创建
        """
        with self.connect() as conn:
            for table_class in self.__class__.__annotations__.values():
                # 动态获取每个表类
                table_class: Table
                # 如果表不存在则创建
                conn.execute(table_class.generate_create_table_sql())  # 执行创建表的 SQL 语句
                conn.commit()
                
                # 创建并存储 Table 对象
                self.create_table_class(table_class)

    def create_table_class(self, table_class: Table):
        """
        动态生成表类实例并作为属性添加到 Database 实例
        
        :param table_class: 表类对象
        """
        # 创建表类对象
        table: Table = table_class(self)
        
        # 使用动态属性将表类对象作为实例的属性
        setattr(self, table.table_name, table)

    # def _get_table_creation_statements(self):
    #     """返回所有表的创建语句"""
    #     return {
    #         'tab_albums': '''CREATE TABLE IF NOT EXISTS "tab_albums" (
    #                             "id" TEXT NOT NULL PRIMARY KEY, 
    #                             "album" TEXT NOT NULL, 
    #                             "artist" TEXT NOT NULL, 
    #                             "url" TEXT NOT NULL, 
    #                             "cover" TEXT NOT NULL, 
    #                             "desc" TEXT NOT NULL, 
    #                             "quality" TEXT NOT NULL, 
    #                             "update_time" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    #                           );''',
    #         'tab_record': '''CREATE TABLE IF NOT EXISTS "tab_record" (
    #                             "id" TEXT NOT NULL PRIMARY KEY, 
    #                             "url" TEXT NOT NULL, 
    #                             "desc" TEXT NOT NULL, 
    #                             "interpreter" TEXT NOT NULL, 
    #                             "search_date" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    #                           );''',
    #         'tab_songs': '''CREATE TABLE IF NOT EXISTS "tab_songs" (
    #                             "id" TEXT NOT NULL PRIMARY KEY, 
    #                             "album_id" TEXT NOT NULL, 
    #                             "no" TEXT NOT NULL, 
    #                             "name" TEXT NOT NULL, 
    #                             "url" TEXT NOT NULL, 
    #                             "update_time" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    #                             FOREIGN KEY ("album_id") REFERENCES "tab_albums" ("id")
    #                           );''',
    #     }


# 示例：使用改进后的 Database 类
# if __name__ == "__main__":
#     db = Database()  # 初始化数据库对象

#     # 创建新表
#     db.create_table('users', ['id', 'name', 'age'])

#     # 获取 'users' 表类并插入数据
#     db.users.insert({'name': 'Alice', 'age': 25})
#     db.users.insert({'name': 'Bob', 'age': 30})

#     # 查询 'users' 表的数据
#     print(db.users.select())

#     # 更新数据
#     db.users.update('name == "Alice"', {'age': 26})

#     # 删除数据
#     db.users.delete('name == "Bob"')

#     # 查询更新后的 'users' 表数据
#     print(db.users.select())