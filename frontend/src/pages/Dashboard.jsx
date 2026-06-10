import { Card, Col, Row, Statistic, Table, Tag, message } from "antd";
import {
  DatabaseOutlined,
  RiseOutlined,
  RollbackOutlined,
  ShoppingCartOutlined,
  TagsOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { getDashboardSummary } from "../api/reports.js";

const statusColor = {
  已完成: "green",
  已退货: "orange",
};

export default function Dashboard() {
  const [summary, setSummary] = useState({
    totals: {},
    recentPurchases: [],
    recentSales: [],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true);
      try {
        const data = await getDashboardSummary();
        setSummary(data);
      } catch (error) {
        message.error(error.message);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  const totals = summary.totals || {};

  const purchaseColumns = [
    { title: "采购单号", dataIndex: "id", width: 150 },
    { title: "供应商", dataIndex: "supplierName" },
    { title: "仓库", dataIndex: "warehouseName", width: 110 },
    { title: "日期", dataIndex: "orderDate", width: 110 },
    { title: "金额", dataIndex: "totalAmount", width: 110, render: (value) => `￥${value}` },
    {
      title: "状态",
      dataIndex: "status",
      width: 90,
      render: (value) => <Tag color={statusColor[value] || "default"}>{value}</Tag>,
    },
  ];

  const salesColumns = [
    { title: "销售单号", dataIndex: "id", width: 150 },
    { title: "客户", dataIndex: "customerName" },
    { title: "仓库", dataIndex: "warehouseName", width: 110 },
    { title: "日期", dataIndex: "orderDate", width: 110 },
    { title: "实付金额", dataIndex: "paidAmount", width: 120, render: (value) => `￥${value}` },
    {
      title: "状态",
      dataIndex: "status",
      width: 90,
      render: (value) => <Tag color={statusColor[value] || "default"}>{value}</Tag>,
    },
  ];

  return (
    <>
      <PageHeader
        title="首页数据看板"
        description="按有效销售和退货分开统计，展示库存、SN、采购、销售与退货的当前业务状态。"
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="配件型号" value={totals.productCount || 0} prefix={<TagsOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="当前库存总数" value={totals.totalStock || 0} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="在库 SN" value={totals.inStockSnCount || 0} prefix={<ShoppingCartOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="已售 SN" value={totals.soldSnCount || 0} prefix={<RiseOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="低库存商品"
              value={totals.lowStockCount || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: totals.lowStockCount ? "#dc2626" : "#16a34a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="今日采购金额" value={totals.todayPurchaseAmount || 0} prefix="￥" />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="今日有效销售"
              value={totals.todayEffectiveSalesAmount || 0}
              prefix="￥"
              valueStyle={{ color: "#16a34a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="今日退货金额"
              value={totals.todayReturnAmount || 0}
              prefix={<RollbackOutlined />}
              valueStyle={{ color: "#f97316" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="section-row">
        <Col xs={24} lg={12}>
          <Card title="最近采购单" loading={loading}>
            <Table
              rowKey="id"
              columns={purchaseColumns}
              dataSource={summary.recentPurchases || []}
              pagination={false}
              size="small"
              scroll={{ x: 760 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="最近销售单" loading={loading}>
            <Table
              rowKey="id"
              columns={salesColumns}
              dataSource={summary.recentSales || []}
              pagination={false}
              size="small"
              scroll={{ x: 760 }}
            />
          </Card>
        </Col>
      </Row>
    </>
  );
}
