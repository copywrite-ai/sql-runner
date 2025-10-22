# SQL 文件执行功能

MySQL Schema Manager 现在支持幂等安全的 SQL 文件执行功能！

## 🚀 新功能概览

### 核心特性
- ✅ **幂等执行**: 重复执行同个 SQL 文件不会出错
- ✅ **智能解析**: 正确处理注释、引号中的分号等复杂 SQL
- ✅ **安全检查**: 执行前检查数据库对象状态
- ✅ **预览模式**: Dry run 模式查看将要执行的操作
- ✅ **详细日志**: 完整的操作记录和错误报告

### 支持的 SQL 类型
- `CREATE TABLE` - 检查表是否存在，存在则跳过
- `ALTER TABLE ADD COLUMN` - 智能字段管理，比较定义
- `CREATE INDEX` / `CREATE UNIQUE INDEX` - 检查索引是否存在
- `INSERT`, `UPDATE`, `DELETE` - 直接执行 DML 语句
- 其他 SQL 语句 - 直接执行

## 📖 快速开始

### 基本用法

```python
from mysql_schema_manager import MySQLSchemaManager

# 初始化
manager = MySQLSchemaManager(
    host='localhost',
    username='your_username',
    password='your_password',
    database='your_database'
)

if manager.connect():
    try:
        # 预览执行
        manager.execute_sql_file('schema.sql', dry_run=True)

        # 实际执行
        success = manager.execute_sql_file('schema.sql')

    finally:
        manager.disconnect()
```

### 命令行工具

```bash
# 执行 SQL 文件
python execute_sql.py schema.sql --database mydb --user root --password mypass

# 预览模式
python execute_sql.py schema.sql --database mydb --dry-run

# 自定义连接参数
python execute_sql.py schema.sql --database mydb --host localhost --port 3306
```

## 🔧 幂等性机制

### CREATE TABLE 处理
```sql
-- 第一次执行：创建表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
-- 日志：Creating table 'users'

-- 第二次执行：跳过
-- 日志：Table 'users' already exists, skipping CREATE TABLE
```

### ALTER TABLE ADD COLUMN 处理
```sql
-- 场景1：字段不存在
ALTER TABLE users ADD COLUMN age INT DEFAULT 0;
-- 日志：Adding column 'age' to table 'users'

-- 场景2：字段存在且定义相同
ALTER TABLE users ADD COLUMN age INT DEFAULT 0;
-- 日志：Column 'age' already exists with same definition

-- 场景3：字段存在但定义不同
ALTER TABLE users ADD COLUMN age VARCHAR(10) DEFAULT 'unknown';
-- 日志：Column 'age' exists with different definition, dropping it first
--       Adding column 'age' to table 'users'
```

### CREATE INDEX 处理
```sql
-- 第一次执行
CREATE INDEX idx_email ON users (email);
-- 日志：Creating INDEX 'idx_email' on table 'users'

-- 第二次执行
-- 日志：Index 'idx_email' already exists on table 'users', skipping CREATE INDEX
```

## 📝 SQL 文件示例

### 复杂架构文件
```sql
-- sample_schema.sql
-- 创建用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    age INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建索引
CREATE INDEX idx_email ON users (email);
CREATE INDEX idx_age ON users (age);
CREATE INDEX idx_status ON users (status);
CREATE INDEX idx_username_email ON users (username, email);
```

### 迁移文件
```sql
-- sample_migration.sql
-- 添加新字段
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN address TEXT;
ALTER TABLE users ADD COLUMN birth_date DATE;

-- 创建新索引
CREATE INDEX idx_phone ON users (phone);
CREATE INDEX idx_birth_date ON users (birth_date);
```

### 数据文件
```sql
-- sample_data.sql
-- 插入测试数据
INSERT INTO users (username, email, age, status) VALUES
('john_doe', 'john@example.com', 25, 'active'),
('jane_smith', 'jane@example.com', 30, 'active'),
('bob_wilson', 'bob@example.com', 35, 'inactive');

-- 更新数据
UPDATE users SET status = 'premium' WHERE age > 28;
```

## 🛠️ 高级功能

### SQL 解析特性

```sql
-- 支持注释
-- 这是单行注释
/* 这是
   多行注释 */
CREATE TABLE test (id INT);

-- 支持引号中的分号
INSERT INTO messages (content) VALUES ('Hello; world; semicolons in text');

-- 支持复杂表定义
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    category_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category_id),
    UNIQUE INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品表';
```

### 错误处理

```python
# 查看执行统计
success = manager.execute_sql_file('complex_schema.sql')
# 输出：SQL file execution completed. Success: 5, Skipped: 2, Errors: 0

# 单个语句错误不会阻止后续执行
# 每个语句都有独立的错误处理和日志记录
```

### 生产环境最佳实践

```python
import os
import logging
from mysql_schema_manager import MySQLSchemaManager

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 环境变量配置
config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'username': os.getenv('DB_USER', 'your_username'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'database': os.getenv('DB_NAME', 'your_database'),
    'port': int(os.getenv('DB_PORT', '3306'))
}

manager = MySQLSchemaManager(**config)

try:
    if manager.connect():
        # 按顺序执行 SQL 文件
        sql_files = [
            '01_schema.sql',
            '02_indexes.sql',
            '03_data.sql'
        ]

        for sql_file in sql_files:
            if os.path.exists(sql_file):
                print(f"Executing {sql_file}...")

                # 先预览
                manager.execute_sql_file(sql_file, dry_run=True)

                # 确认后执行
                if input(f"Execute {sql_file}? (y/n): ").lower() == 'y':
                    if manager.execute_sql_file(sql_file):
                        print(f"✓ {sql_file} completed successfully")
                    else:
                        print(f"✗ {sql_file} execution failed")
                        break
                else:
                    print(f"⚠️ {sql_file} skipped")
            else:
                print(f"⚠️ {sql_file} not found, skipping")

finally:
    manager.disconnect()
```

## 📊 示例文件

运行演示脚本来生成示例文件：

```bash
python sql_file_demo.py
```

将会创建以下示例文件：
- `sample_schema.sql` - 基础用户表架构
- `sample_migration.sql` - 迁移脚本示例
- `sample_data.sql` - 数据操作示例
- `complex_schema.sql` - 复杂多表架构

## 🧪 测试

```bash
# 运行完整测试套件（包含新的 SQL 文件测试）
python test_mysql_schema_manager.py

# 测试覆盖：
# ✅ SQL 文件解析
# ✅ 幂等性检查
# ✅ 错误处理
# ✅ Dry run 模式
# ✅ 复杂 SQL 语句
# ✅ 注释和引号处理
```

## 📝 API 参考

### 新增方法

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `execute_sql_file(file_path, dry_run=False)` | 执行 SQL 文件 | `file_path: str`, `dry_run: bool` | `bool` |
| `parse_sql_file(file_path)` | 解析 SQL 文件 | `file_path: str` | `List[str]` |
| `_clean_sql_content(content)` | 清理 SQL 内容 | `content: str` | `str` |
| `_extract_table_name_from_create(sql)` | 提取表名 | `sql: str` | `str or None` |
| `_extract_column_info_from_alter(sql)` | 提取列信息 | `sql: str` | `tuple or None` |
| `_extract_index_info_from_create(sql)` | 提取索引信息 | `sql: str` | `tuple or None` |

### 内部处理方法

| 方法 | 描述 |
|------|------|
| `_handle_create_table(statement, dry_run)` | 处理 CREATE TABLE |
| `_handle_add_column(statement, dry_run)` | 处理 ALTER TABLE ADD COLUMN |
| `_handle_create_index(statement, dry_run)` | 处理 CREATE INDEX |
| `_handle_dml_statement(statement, dry_run)` | 处理 DML 语句 |

## 🔒 安全特性

- **参数化查询**: 防止 SQL 注入
- **文件路径验证**: 检查文件存在性
- **错误隔离**: 单个语句错误不影响其他语句
- **事务支持**: 失败时自动回滚
- **详细日志**: 完整的操作审计

## 🚨 注意事项

1. **备份重要数据**: 执行前请备份重要数据
2. **测试环境验证**: 在生产环境使用前先在测试环境验证
3. **权限要求**: 需要适当的数据库权限
4. **大型文件**: 对于大型 SQL 文件，考虑分批执行

## 📈 性能考虑

- 大型 SQL 文件会被逐个语句执行，避免内存问题
- 每个语句都有独立的错误处理
- 日志记录可以帮助监控执行进度
- 建议对大型架构使用分阶段执行

现在您可以安全地重复执行任何 SQL 文件，系统会智能地跳过已存在的对象！