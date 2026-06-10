import { Card, Col, Empty, Row, Table, Tag, message } from "antd";
import ReactECharts from "echarts-for-react";
import { useEffect, useMemo, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { getReportOverview } from "../api/reports.js";

const chartColors = ["#2563eb", "#f97316", "#16a34a", "#dc2626", "#7c3aed"];

export default function Reports() {
  const [overview, setOverview] = useState({
    salesTrend: [],
    categorySales: [],
    categoryStock: [],
    hotProducts: [],
    returnedOrders: [],
    warningSummary: [],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadReports() {
      setLoading(true);
      try {
        const data = await getReportOverview({ days: 7 });
        setOverview(data);
      } catch (error) {
        message.error(error.message);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  const salesTrend = overview.salesTrend || [];
  const categorySales = overview.categorySales || [];
  const categoryStock = overview.categoryStock || [];
  const hotProducts = overview.hotProducts || [];
  const returnedOrders = overview.returnedOrders || [];
  const warningSummary = overview.warningSummary || [];

  const trendOption = useMemo(
    () => ({
      color: chartColors,
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 46, right: 20, top: 48, bottom: 32 },
      xAxis: { type: "category", data: salesTrend.map((item) => item.date) },
      yAxis: { type: "value" },
      series: [
        {
          name: "有效销售金额",
          type: "line",
          smooth: true,
          data: salesTrend.map((item) => item.effectiveSalesAmount),
          areaStyle: { opacity: 0.14 },
        },
        {
          name: "退货金额",
          type: "line",
          smooth: true,
          data: salesTrend.map((item) => item.returnAmount),
          areaStyle: { opacity: 0.1 },
        },
      ],
    }),
    [salesTrend]
  );

  const categorySalesOption = useMemo(
    () => ({
      color: chartColors,
      tooltip: { trigger: "item" },
      legend: { bottom: 0 },
      series: [
        {
          name: "有效销售金额",
          type: "pie",
          radius: ["42%", "68%"],
          center: ["50%", "44%"],
          data: categorySales.map((item) => ({
            name: item.categoryName,
            value: item.salesAmount,
          })),
        },
      ],
    }),
    [categorySales]
  );

  const stockOption = useMemo(
    () => ({
      color: ["#2563eb"],
      tooltip: { trigger: "axis" },
      grid: { left: 46, right: 20, top: 28, bottom: 48 },
      xAxis: {
        type: "category",
        data: categoryStock.map((item) => item.categoryName),
        axisLabel: { interval: 0 },
      },
      yAxis: { type: "value" },
      series: [
        {
          name: "库存数量",
          type: "bar",
          data: categoryStock.map((item) => item.stockQuantity),
          barMaxWidth: 48,
        },
      ],
    }),
    [categoryStock]
  );

  const warningOption = useMemo(
    () => ({
      color: ["#dc2626"],
      tooltip: { trigger: "axis" },
      grid: { left: 46, right: 20, top: 28, bottom: 48 },
      xAxis: {
        type: "category",
        data: warningSummary.map((item) => item.categoryName),
        axisLabel: { interval: 0 },
      },
      yAxis: { type: "value" },
      series: [
        {
          name: "低库存数量",
          type: "bar",
          data: warningSummary.map((item) => item.warningCount),
          barMaxWidth: 48,
        },
      ],
    }),
    [warningSummary]
  );

  const hotColumns = [
    { title: "配件名称", dataIndex: "productName" },
    { title: "分类", dataIndex: "categoryName", width: 100 },
    { title: "品牌", dataIndex: "brandName", width: 120 },
    { title: "有效销量", dataIndex: "salesQuantity", width: 100 },
    { title: "有效销售额", dataIndex: "salesAmount", width: 120, render: (value) => `￥${value}` },
  ];

  const returnColumns = [
    { title: "销售单号", dataIndex: "id", width: 160 },
    { title: "客户", dataIndex: "customerName" },
    { title: "销售日期", dataIndex: "orderDate", width: 120 },
    { title: "退货金额", dataIndex: "paidAmount", width: 120, render: (value) => `￥${value}` },
    {
      title: "状态",
      dataIndex: "status",
      width: 100,
      render: (value) => <Tag color="orange">{value}</Tag>,
    },
  ];

  return (
    <>
      <PageHeader
        title="统计报表"
        description="销售统计只将已完成订单计入有效销售，已退货订单单独统计，避免退货后销售额虚高。"
      />
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="近 7 天销售与退货趋势" loading={loading}>
            <ReactECharts option={trendOption} style={{ height: 320 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="各类别有效销售金额占比" loading={loading}>
            {categorySales.length ? (
              <ReactECharts option={categorySalesOption} style={{ height: 320 }} />
            ) : (
              <Empty description="暂无已完成销售数据" style={{ padding: 72 }} />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="库存数量按类别统计" loading={loading}>
            <ReactECharts option={stockOption} style={{ height: 320 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="低库存预警按类别统计" loading={loading}>
            {warningSummary.length ? (
              <ReactECharts option={warningOption} style={{ height: 320 }} />
            ) : (
              <Empty description="暂无低库存预警" style={{ padding: 72 }} />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="热销商品排行">
            <Table
              rowKey="productId"
              columns={hotColumns}
              dataSource={hotProducts}
              loading={loading}
              pagination={false}
              scroll={{ x: 760 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="最近退货销售单">
            <Table
              rowKey="id"
              columns={returnColumns}
              dataSource={returnedOrders}
              loading={loading}
              pagination={false}
              scroll={{ x: 620 }}
            />
          </Card>
        </Col>
      </Row>
    </>
  );
}
