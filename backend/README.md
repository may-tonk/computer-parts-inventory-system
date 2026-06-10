# 电脑配件进销存 Flask 后端

## 1. 创建虚拟环境

在 PyCharm 中打开 `D:\React_python_Mysql\backend`，创建项目虚拟环境 `.venv`。

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 3. 配置数据库

复制 `.env.example` 为 `.env`，把数据库同学提供的连接信息填进去：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=你的用户名
DB_PASSWORD=你的密码
DB_NAME=数据库名
```

## 4. 启动服务

```bash
python app.py
```

启动后访问：

```text
http://127.0.0.1:5000/api/health
http://127.0.0.1:5000/api/db-test
```
