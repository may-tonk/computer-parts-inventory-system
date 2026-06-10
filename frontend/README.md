# 电脑配件进销存管理系统前端

技术栈：

- React + Vite
- Ant Design
- React Router
- Axios
- ECharts

## 启动

```bash
npm install
npm run dev
```

## 后端接口地址

复制 `.env.example` 为 `.env.local`，修改：

```text
VITE_API_BASE_URL=http://后端电脑IP:5000/api
```

如果后端就在本机运行，可以使用：

```text
VITE_API_BASE_URL=http://localhost:5000/api
```

React 前端不直接连接 MySQL，只通过 Python 后端接口获取 JSON 数据。
