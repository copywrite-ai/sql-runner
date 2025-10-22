# MySQL Schema Manager

一个用于安全 MySQL 数据库架构操作的 Python 脚本，支持存在性检查和智能操作。

## 功能特性

### 🛡️ 安全操作
- **存在性检查**: 所有操作前都会检查对象是否存在
- **智能更新**: 自动比较列定义，避免不必要的修改
- **事务支持**: 操作失败时自动回滚
- **SQL 注入防护**: 使用参数化查询

### 📋 支持的操作

#### 1. 创建表 (CREATE TABLE)
- 自动检查表是否存在
- 存在则先 `DROP TABLE` 再创建
- 支持完整的表定义语法

#### 2. 修改表 (ALTER TABLE)
- 智能字段管理：
  - 字段不存在 → 直接添加
  - 字段存在但属性不同 → 先删除再添加
  - 字段存在且属性相同 → 跳过操作
- 支持复杂列定义 (NOT NULL, DEFAULT, UNIQUE, AUTO_INCREMENT)

#### 3. 创建索引 (CREATE INDEX)
- 支持所有索引类型：INDEX, UNIQUE, FULLTEXT, SPATIAL
- 自动检查索引是否存在
- 存在则先删除再创建
- 支持单列和复合索引

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from mysql_schema_manager import MySQLSchemaManager

# 1. 初始化管理器
config = {
    'host': 'localhost',
    'username': 'your_username',
    'password': 'your_password',
    'database': 'your_database',
    'port': 3306
}

manager = MySQLSchemaManager(**config)

# 2. 连接数据库
if manager.connect():
    print("数据库连接成功")

    try:
        # 3. 创建表 (存在则先删除)
        create_sql = """
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        manager.create_table_with_drop('users', create_sql)

        # 4. 添加字段 (智能检查)
        manager.alter_table_add_column('users', 'age', 'INT DEFAULT 0')
        manager.alter_table_add_column('users', 'status', "VARCHAR(20) DEFAULT 'active'")

        # 5. 创建索引 (存在则先删除)
        manager.create_index_with_check('users', 'idx_email', ['email'])
        manager.create_index_with_check('users', 'idx_name_email', ['username', 'email'])
        manager.create_index_with_check('users', 'idx_age', ['age'], unique=False)

        print("所有操作完成!")

    finally:
        # 6. 关闭连接
        manager.disconnect()
```

## API 参考

### MySQLSchemaManager

#### 初始化

```python
manager = MySQLSchemaManager(
    host='localhost',
    username='your_username',
    password='your_password',
    database='your_database',
    port=3306
)
```

#### 连接管理

| 方法 | 描述 | 返回值 |
|------|------|--------|
| `connect()` | 建立数据库连接 | `bool` |
| `disconnect()` | 关闭数据库连接 | `void` |

#### 表操作

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `table_exists(table_name)` | 检查表是否存在 | `table_name: str` | `bool` |
| `create_table_with_drop(table_name, create_sql)` | 创建表 (存在则先删除) | `table_name: str`, `create_sql: str` | `bool` |

#### 列操作

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `column_exists(table_name, column_name)` | 检查列是否存在 | `table_name: str`, `column_name: str` | `bool` |
| `get_column_definition(table_name, column_name)` | 获取列定义 | `table_name: str`, `column_name: str` | `str` or `None` |
| `alter_table_add_column(table_name, column_name, column_definition)` | 添加列 (智能检查) | `table_name: str`, `column_name: str`, `column_definition: str` | `bool` |

#### 索引操作

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `index_exists(table_name, index_name)` | 检查索引是否存在 | `table_name: str`, `index_name: str` | `bool` |
| `create_index_with_check(table_name, index_name, column_names, index_type, unique)` | 创建索引 (存在则先删除) | `table_name: str`, `index_name: str`, `column_names: List[str]`, `index_type: str`, `unique: bool` | `bool` |

## 使用示例

### 示例 1: 创建用户表

```python
# 完整的用户表创建
create_user_table = """
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

manager.create_table_with_drop('users', create_user_table)
```

### 示例 2: 动态添加字段

```python
# 添加新字段 (如果不存在)
manager.alter_table_add_column('users', 'profile_image', 'VARCHAR(255)')

# 修改现有字段 (会先删除再添加)
manager.alter_table_add_column('users', 'age', 'TINYINT UNSIGNED DEFAULT 0')

# 添加带约束的字段
manager.alter_table_add_column('users', 'email_verified', 'BOOLEAN DEFAULT FALSE')
```

### 示例 3: 创建各种索引

```python
# 普通索引
manager.create_index_with_check('users', 'idx_email', ['email'])

# 唯一索引
manager.create_index_with_check('users', 'idx_username', ['username'], unique=True)

# 复合索引
manager.create_index_with_check('users', 'idx_status_age', ['status', 'age'])

# 全文索引 (需要 FULLTEXT 类型)
manager.create_index_with_check('articles', 'idx_content', ['title', 'content'],
                               index_type='FULLTEXT')
```

## 内部机制

### 存在性检查

脚本使用 `information_schema` 数据库进行对象存在性检查：

```sql
-- 检查表
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = ? AND table_name = ?

-- 检查列
SELECT COUNT(*) FROM information_schema.columns
WHERE table_schema = ? AND table_name = ? AND column_name = ?

-- 检查索引
SELECT COUNT(*) FROM information_schema.statistics
WHERE table_schema = ? AND table_name = ? AND index_name = ?
```

### 列定义比较

自动标准化列定义进行比较，忽略格式差异：

```python
# 这两个定义被认为是相同的
def1 = "VARCHAR(255) NOT NULL DEFAULT 'test'"
def2 = "  varchar(255)   not  null   default 'test'  "
```

### 事务处理

所有数据库操作都在事务中执行，失败时自动回滚：

```python
try:
    cursor.execute(query, params)
    self.connection.commit()
    return True
except Error as e:
    self.connection.rollback()
    return False
```

## 日志记录

脚本使用 Python 标准库 `logging` 记录操作：

```python
import logging
logging.basicConfig(level=logging.INFO)

# 日志示例
INFO:mysql_schema_manager:Successfully connected to MySQL database 'test_db'
INFO:mysql_schema_manager:Table 'users' exists, dropping it first
INFO:mysql_schema_manager:Creating table 'users'
INFO:mysql_schema_manager:Column 'age' already exists with same definition in table 'users'
INFO:mysql_schema_manager:Adding column 'profile_image' to table 'users'
```

## 测试

运行测试套件：

```bash
# 运行所有测试
python test_mysql_schema_manager.py

# 运行演示 (无需数据库连接)
python demo_usage.py
```

测试覆盖：
- ✅ 语法检查
- ✅ 类初始化
- ✅ 连接管理
- ✅ 存在性检查逻辑
- ✅ SQL 生成
- ✅ 错误处理
- ✅ 安全性验证

## 文件结构

```
sql-runner/
├── mysql_schema_manager.py    # 主要功能模块
├── requirements.txt           # 依赖包
├── test_mysql_schema_manager.py  # 测试套件
├── demo_usage.py              # API 演示
└── README.md                  # 文档
```

## 依赖要求

```
mysql-connector-python==8.2.0
```

## 注意事项

1. **权限要求**: 需要 MySQL 用户具有以下权限：
   - SELECT (information_schema)
   - CREATE, DROP, ALTER (目标数据库)
   - INDEX (目标数据库)

2. **数据安全**:
   - 脚本会删除已存在的对象，请谨慎使用
   - 建议在生产环境使用前先在测试环境验证

3. **兼容性**:
   - 支持 MySQL 5.7+
   - 支持 MariaDB 10.2+
   - Python 3.7+

## 常见问题

### Q: 如何处理大数据表？
A: 对于大表，ALTER TABLE 操作可能会锁表。建议在低峰期执行，或使用 pt-online-schema-change 等工具。

### Q: 支持外键约束吗？
A: 支持，可以在 CREATE TABLE 语句中包含外键定义。

### Q: 如何自定义日志级别？
A: 修改 logging 配置：
```python
import logging
logging.basicConfig(level=logging.DEBUG)  # 更详细的日志
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0 (2025-01-22)
- ✅ 初始版本发布
- ✅ 支持表、列、索引的安全操作
- ✅ 完整的测试覆盖
- ✅ 详细的文档和示例