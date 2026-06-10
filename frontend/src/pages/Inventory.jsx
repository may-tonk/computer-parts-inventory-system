import { Alert, Card, Descriptions, Input, Select, Space, Table, Tabs, Tag, message } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { getCategories, getWarehouses } from "../api/masterData.js";
import {
  getInventoryWarnings,
  getSnDetail,
  getStockDetails,
} from "../api/inventory.js";

const statusColor = {
  正常: "green",
  低库存: "red",
  在库: "green",
  锁定: "orange",
  已售: "blue",
  已退货: "red",
};

export default function Inventory() {
  const [keyword, setKeyword] = useState("");
  const [categoryId, setCategoryId] = useState();
  const [warehouseId, setWarehouseId] = useState();
  const [snKeyword, setSnKeyword] = useState("");
  const [categories, setCategories] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [stockData, setStockData] = useState([]);
  const [inventoryWarnings, setInventoryWarnings] = useState([]);
  const [snDetail, setSnDetail] = useState(null);
  const [stockLoading, setStockLoading] = useState(false);
  const [warningLoading, setWarningLoading] = useState(false);
  const [snLoading, setSnLoading] = useState(false);

  const categoryOptions = useMemo(
    () => categories.map((item) => ({ label: item.name, value: item.id })),
    [categories]
  );

  const warehouseOptions = useMemo(
    () => warehouses.map((item) => ({ label: item.name, value: item.id })),
    [warehouses]
  );

  useEffect(() => {
    async function loadOptions() {
      try {
        const [categoryData, warehouseData] = await Promise.all([
          getCategories(),
          getWarehouses(),
        ]);
        setCategories(categoryData);
        setWarehouses(warehouseData);
      } catch (error) {
        message.error(error.message);
      }
    }
    loadOptions();
  }, []);

  useEffect(() => {
    async function loadStock() {
      setStockLoading(true);
      try {
        const data = await getStockDetails({
          keyword: keyword || undefined,
          categoryId: categoryId || undefined,
          warehouseId: warehouseId || undefined,
        });
        setStockData(data);
      } catch (error) {
        message.error(error.message);
      } finally {
        setStockLoading(false);
      }
    }
    loadStock();
  }, [keyword, categoryId, warehouseId]);

  useEffect(() => {
    async function loadWarnings() {
      setWarningLoading(true);
      try {
        const data = await getInventoryWarnings();
        setInventoryWarnings(data);
      } catch (error) {
        message.error(error.message);
      } finally {
        setWarningLoading(false);
      }
    }
    loadWarnings();
  }, []);

  async function handleSnSearch(value) {
    const nextValue = value.trim();
    setSnKeyword(nextValue);
    setSnDetail(null);
    if (!nextValue) return;

    setSnLoading(true);
    try {
      const data = await getSnDetail(nextValue);
      setSnDetail(data);
    } catch (error) {
      message.error(error.message);
    } finally {
      setSnLoading(false);
    }
  }

  const stockColumns = [
    { title: "配件名称", dataIndex: "productName", width: 240 },
    { title: "分类", dataIndex: "categoryName" },
    { title: "品牌", dataIndex: "brandName" },
    { title: "仓库", dataIndex: "warehouseName" },
    { title: "库存数量", dataIndex: "quantity" },
    { title: "预警值", dataIndex: "warningValue" },
    {
      title: "状态",
      dataIndex: "status",
      render: (value) => <Tag color={statusColor[value]}>{value}</Tag>,
    },
    { title: "更新时间", dataIndex: "updatedAt", width: 180 },
  ];

  return (
    <>
      <PageHeader
        title="库存查询"
        description="对应 stock、product_sn、v_stock_detail、v_inventory_warning，区分汇总库存和 SN 单件追踪。"
      />
      <Tabs
        items={[
          {
            key: "stock",
            label: "库存汇总",
            children: (
              <Card>
                <Space wrap className="toolbar">
                  <Input
                    allowClear
                    prefix={<SearchOutlined />}
                    placeholder="搜索配件 / 品牌"
                    value={keyword}
                    onChange={(event) => setKeyword(event.target.value)}
                    style={{ width: 260 }}
                  />
                  <Select
                    allowClear
                    placeholder="分类"
                    value={categoryId}
                    onChange={setCategoryId}
                    style={{ width: 160 }}
                    options={categoryOptions}
                  />
                  <Select
                    allowClear
                    placeholder="仓库"
                    value={warehouseId}
                    onChange={setWarehouseId}
                    style={{ width: 160 }}
                    options={warehouseOptions}
                  />
                </Space>
                <Table
                  rowKey={(record) => `${record.productId}-${record.warehouseId}`}
                  columns={stockColumns}
                  dataSource={stockData}
                  loading={stockLoading}
                  pagination={{ pageSize: 8 }}
                  scroll={{ x: 1080 }}
                />
              </Card>
            ),
          },
          {
            key: "sn",
            label: "SN 单件查询",
            children: (
              <Card>
                <Space wrap className="toolbar">
                  <Input.Search
                    allowClear
                    prefix={<SearchOutlined />}
                    placeholder="输入完整 SN 码"
                    value={snKeyword}
                    onChange={(event) => setSnKeyword(event.target.value)}
                    onSearch={handleSnSearch}
                    loading={snLoading}
                    style={{ width: 360 }}
                  />
                </Space>
                {snDetail ? (
                  <Space direction="vertical" size={16} style={{ width: "100%" }}>
                    <Descriptions bordered column={2} className="sn-detail">
                      <Descriptions.Item label="SN 码">{snDetail.snCode}</Descriptions.Item>
                      <Descriptions.Item label="当前状态">
                        <Tag color={statusColor[snDetail.status]}>{snDetail.status}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="配件名称">{snDetail.productName}</Descriptions.Item>
                      <Descriptions.Item label="分类">{snDetail.categoryName}</Descriptions.Item>
                      <Descriptions.Item label="品牌">{snDetail.brandName}</Descriptions.Item>
                      <Descriptions.Item label="型号">{snDetail.model || "-"}</Descriptions.Item>
                      <Descriptions.Item label="当前仓库">{snDetail.warehouseName}</Descriptions.Item>
                      <Descriptions.Item label="批次号">{snDetail.batchNo || "-"}</Descriptions.Item>
                      <Descriptions.Item label="入库日期">{snDetail.inboundDate}</Descriptions.Item>
                      <Descriptions.Item label="保修截止">{snDetail.warrantyEndDate}</Descriptions.Item>
                    </Descriptions>
                    <Descriptions bordered column={2} title="入库来源">
                      <Descriptions.Item label="入库单号">{snDetail.inboundNo || "-"}</Descriptions.Item>
                      <Descriptions.Item label="采购单号">{snDetail.purchaseId || "-"}</Descriptions.Item>
                      <Descriptions.Item label="供应商">{snDetail.supplierName || "-"}</Descriptions.Item>
                      <Descriptions.Item label="采购日期">{snDetail.purchaseDate || "-"}</Descriptions.Item>
                    </Descriptions>
                    <Descriptions bordered column={2} title="销售去向">
                      <Descriptions.Item label="出库单号">{snDetail.outboundNo || "-"}</Descriptions.Item>
                      <Descriptions.Item label="销售单号">{snDetail.salesId || "-"}</Descriptions.Item>
                      <Descriptions.Item label="销售单状态">
                        {snDetail.salesStatus ? (
                          <Tag color={statusColor[snDetail.salesStatus] || "default"}>
                            {snDetail.salesStatus}
                          </Tag>
                        ) : (
                          "-"
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="客户">{snDetail.customerName || "-"}</Descriptions.Item>
                      <Descriptions.Item label="销售日期">{snDetail.salesDate || "-"}</Descriptions.Item>
                      <Descriptions.Item label="销售单价">
                        {snDetail.salesUnitPrice == null ? "-" : `￥${snDetail.salesUnitPrice}`}
                      </Descriptions.Item>
                      <Descriptions.Item label="销售单实付">
                        {snDetail.salesPaidAmount == null ? "-" : `￥${snDetail.salesPaidAmount}`}
                      </Descriptions.Item>
                    </Descriptions>
                  </Space>
                ) : null}
              </Card>
            ),
          },
          {
            key: "warning",
            label: "库存预警",
            children: (
              <Card loading={warningLoading}>
                {inventoryWarnings.length ? (
                  inventoryWarnings.map((item) => (
                    <Alert
                      key={`${item.productId}-${item.warehouseId}`}
                      className="warning-item"
                      type="warning"
                      showIcon
                      message={`${item.productName} 库存低于预警值`}
                      description={`${item.warehouseName} 当前库存 ${item.quantity}，预警值 ${item.warningValue}`}
                    />
                  ))
                ) : (
                  <Alert type="success" showIcon message="暂无库存预警" />
                )}
              </Card>
            ),
          },
        ]}
      />
    </>
  );
}
