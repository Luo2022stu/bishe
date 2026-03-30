"""
测试 SQL Server 连接
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# 获取配置
server = os.getenv('MSSQL_HOST', 'localhost')
port = os.getenv('MSSQL_PORT', '1433')
database = os.getenv('MSSQL_DATABASE', 'lost_found')
username = os.getenv('MSSQL_USER', 'sa')
password = os.getenv('MSSQL_PASSWORD', '')
driver = os.getenv('MSSQL_DRIVER', 'ODBC Driver 17 for SQL Server')

# 构建连接字符串
conn_str = f'DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password}'

print(f'正在连接 SQL Server...')
print(f'服务器: {server}:{port}')
print(f'数据库: {database}')
print(f'用户: {username}')
print('-' * 50)

try:
    # 尝试连接
    conn = pyodbc.connect(conn_str)
    print('✅ 连接成功！')
    
    # 测试查询
    cursor = conn.cursor()
    cursor.execute('SELECT @@VERSION')
    version = cursor.fetchone()
    print(f'SQL Server 版本: {version[0]}')
    
    # 检查数据库是否存在
    cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{database}'")
    db_exists = cursor.fetchone()
    if db_exists:
        print(f'✅ 数据库 "{database}" 存在')
    else:
        print(f'❌ 数据库 "{database}" 不存在，请先创建')
    
    conn.close()
    
except pyodbc.Error as e:
    print(f'❌ 连接失败！')
    print(f'错误代码: {e.args[0]}')
    print(f'错误信息: {e.args[1]}')
    print('\n常见问题：')
    print('1. 检查 SQL Server 服务是否启动')
    print('2. 检查用户名和密码是否正确')
    print('3. 检查数据库是否已创建')
    print('4. 检查 ODBC 驱动是否已安装')
    print('5. 检查防火墙设置')
    
except Exception as e:
    print(f'❌ 发生未知错误: {e}')
