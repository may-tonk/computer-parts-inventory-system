# 电脑配件进销存管理系统

本项目采用前后端分离结构：

```text
React + Vite 前端
Flask 后端 API
MySQL 数据库
```

## 启动后端

```powershell
cd D:\React_python_Mysql\backend
.\.venv\Scripts\python.exe app.py
```

后端默认地址：

```text
http://127.0.0.1:5000
```

检查接口：

```text
http://127.0.0.1:5000/api/health
http://127.0.0.1:5000/api/db-test
```

注意：如果后端需要访问局域网 MySQL，Windows 可能会拦截普通沙盒进程的网络访问。出现 `WinError 10013` 时，请关闭旧的 Flask 进程后，用正常终端重新启动后端。

## 启动前端

```powershell
cd D:\React_python_Mysql\frontend
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

## 当前约定

```text
SN 由 Flask 后端生成
数据库不写 SN 生成触发器
product_sn.sn_code 保持唯一约束
stock(product_id, warehouse_id) 保持唯一约束
库存数量以 stock 为汇总
单件追踪以 product_sn 为准
```

已售出的 SN 仍然是历史实物编号，不能再次生成或复用。后端生成 SN 时需要基于 `product_sn.sn_code` 全表查重，并由数据库唯一约束兜底。

## 演示数据

用于扩充 SN 和同步库存的脚本：

```text
database\06_expand_sn_demo_data.sql
```

如果数据库账号没有 `CREATE TEMPORARY TABLE` 权限，可以使用后端脚本执行同样的扩充逻辑：

```powershell
cd D:\React_python_Mysql\backend
.\.venv\Scripts\python.exe scripts\expand_sn_demo_data.py
```

这些脚本不会删除已有数据，会补充更多“在库”SN，并额外保留少量“锁定”SN 供销售校验测试使用。
