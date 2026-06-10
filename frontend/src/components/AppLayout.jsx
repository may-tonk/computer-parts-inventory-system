import {
  AppstoreOutlined,
  BarChartOutlined,
  DatabaseOutlined,
  HomeOutlined,
  InboxOutlined,
  ShoppingCartOutlined,
  ShoppingOutlined,
} from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: "/dashboard", icon: <HomeOutlined />, label: "首页看板" },
  { key: "/accessories", icon: <AppstoreOutlined />, label: "配件管理" },
  { key: "/inventory", icon: <DatabaseOutlined />, label: "库存查询" },
  { key: "/purchases", icon: <ShoppingCartOutlined />, label: "采购管理" },
  { key: "/sales", icon: <ShoppingOutlined />, label: "销售管理" },
  { key: "/reports", icon: <BarChartOutlined />, label: "统计报表" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Layout className="app-shell">
      <Sider width={232} className="app-sider">
        <div className="brand">
          <InboxOutlined className="brand-icon" />
          <div>
            <Typography.Text strong>电脑配件进销存</Typography.Text>
            <span>React 前端演示</span>
          </div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Typography.Title level={4}>电脑配件进销存管理系统</Typography.Title>
          <Typography.Text type="secondary">
            前端通过 Python API 获取 MySQL 数据
          </Typography.Text>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
