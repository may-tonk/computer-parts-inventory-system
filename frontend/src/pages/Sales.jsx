import {
  Button,
  Card,
  Descriptions,
  Drawer,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  message,
} from "antd";
import { DeleteOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { getSnList } from "../api/inventory.js";
import { getCustomers, getWarehouses } from "../api/masterData.js";
import { createSale, getSaleDetail, getSales, returnSale } from "../api/orders.js";

const statusOptions = [
  { label: "已完成", value: "已完成" },
  { label: "已退货", value: "已退货" },
];

const statusColor = {
  已完成: "green",
  已退货: "orange",
  在库: "green",
  已售: "blue",
};

export default function Sales() {
  const [form] = Form.useForm();
  const [filterForm] = Form.useForm();
  const [current, setCurrent] = useState(null);
  const [open, setOpen] = useState(false);
  const [saleList, setSaleList] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [snList, setSnList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [snLoading, setSnLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [returningId, setReturningId] = useState(null);
  const selectedWarehouseId = Form.useWatch("warehouseId", form);

  const customerOptions = useMemo(
    () => customers.map((item) => ({ label: item.name, value: item.id })),
    [customers]
  );

  const warehouseOptions = useMemo(
    () => warehouses.map((item) => ({ label: item.name, value: item.id })),
    [warehouses]
  );

  const snOptions = useMemo(
    () =>
      snList.map((item) => ({
        label: `${item.snCode} / ${item.productName} / ${item.warehouseName}`,
        value: item.snCode,
      })),
    [snList]
  );

  async function loadSales(params = filterForm.getFieldsValue()) {
    setLoading(true);
    try {
      const data = await getSales(params);
      setSaleList(data);
    } catch (error) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSales({});
  }, []);

  useEffect(() => {
    async function loadOptions() {
      try {
        const [customerData, warehouseData] = await Promise.all([
          getCustomers(),
          getWarehouses(),
        ]);
        setCustomers(customerData);
        setWarehouses(warehouseData);
      } catch (error) {
        message.error(error.message);
      }
    }
    loadOptions();
  }, []);

  useEffect(() => {
    async function loadSnOptions() {
      if (!selectedWarehouseId) {
        setSnList([]);
        return;
      }
      setSnLoading(true);
      try {
        const data = await getSnList({
          warehouseId: selectedWarehouseId,
          status: "在库",
        });
        setSnList(data);
      } catch (error) {
        message.error(error.message);
      } finally {
        setSnLoading(false);
      }
    }
    loadSnOptions();
  }, [selectedWarehouseId]);

  async function handleSearch() {
    await loadSales(filterForm.getFieldsValue());
  }

  async function handleReset() {
    filterForm.resetFields();
    await loadSales({});
  }

  async function handleView(record) {
    setCurrent(record);
    setDetailLoading(true);
    try {
      const data = await getSaleDetail(record.id);
      setCurrent(data);
    } catch (error) {
      message.error(error.message);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleSubmit() {
    const values = await form.validateFields();
    setSaving(true);
    try {
      const result = await createSale(values);
      message.success(`销售出库成功，售出 ${result.soldSnCodes.length} 个 SN`);
      setOpen(false);
      form.resetFields();
      setSnList([]);
      await loadSales();
    } catch (error) {
      message.error(error.message);
    } finally {
      setSaving(false);
    }
  }

  function handleReturn(record) {
    Modal.confirm({
      title: "确认整单退货",
      content: `销售单 ${record.id} 退货后，相关 SN 会重新变为在库，库存数量会加回。`,
      okText: "确认退货",
      cancelText: "取消",
      okButtonProps: { danger: true },
      async onOk() {
        setReturningId(record.id);
        try {
          const result = await returnSale(record.id);
          message.success(`退货成功，退回 ${result.returnedSnCodes.length} 个 SN`);
          if (current?.id === record.id) {
            const detail = await getSaleDetail(record.id);
            setCurrent(detail);
          }
          await loadSales();
        } catch (error) {
          message.error(error.message);
        } finally {
          setReturningId(null);
        }
      },
    });
  }

  const columns = [
    { title: "销售单号", dataIndex: "id", width: 160 },
    { title: "客户", dataIndex: "customerName" },
    { title: "销售员", dataIndex: "sellerName" },
    { title: "仓库", dataIndex: "warehouseName" },
    { title: "销售日期", dataIndex: "orderDate" },
    { title: "销售金额", dataIndex: "totalAmount", render: (value) => `￥${value}` },
    { title: "折扣率", dataIndex: "discountRate", render: (value) => `${Number(value) * 100}%` },
    { title: "实付金额", dataIndex: "paidAmount", render: (value) => `￥${value}` },
    {
      title: "状态",
      dataIndex: "status",
      render: (value) => <Tag color={statusColor[value] || "default"}>{value}</Tag>,
    },
    {
      title: "操作",
      width: 150,
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => handleView(record)}>
            查看
          </Button>
          <Button
            type="link"
            danger
            disabled={record.status !== "已完成"}
            loading={returningId === record.id}
            onClick={() => handleReturn(record)}
          >
            退货
          </Button>
        </Space>
      ),
    },
  ];

  const detailColumns = [
    { title: "SN 码", dataIndex: "snCode", width: 190 },
    { title: "配件", dataIndex: "productName" },
    { title: "分类", dataIndex: "categoryName", width: 90 },
    { title: "品牌", dataIndex: "brandName", width: 110 },
    { title: "单价", dataIndex: "unitPrice", width: 100, render: (value) => `￥${value}` },
    { title: "小计", dataIndex: "subtotal", width: 100, render: (value) => `￥${value}` },
    {
      title: "SN 状态",
      dataIndex: "snStatus",
      width: 100,
      render: (value) => <Tag color={statusColor[value] || "default"}>{value}</Tag>,
    },
  ];

  return (
    <>
      <PageHeader
        title="销售管理"
        description="对应 sales_order、sales_detail、outbound_order、outbound_detail。销售单按 SN 码选择具体实物，由后端校验库存。"
        action={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            新建销售单
          </Button>
        }
      />
      <Card>
        <Form form={filterForm} layout="inline" className="toolbar">
          <Form.Item name="keyword">
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="销售单号 / 客户"
              style={{ width: 220 }}
            />
          </Form.Item>
          <Form.Item name="customerId">
            <Select allowClear placeholder="客户" options={customerOptions} style={{ width: 180 }} />
          </Form.Item>
          <Form.Item name="sellerId">
            <InputNumber min={1} placeholder="销售员 ID" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="warehouseId">
            <Select allowClear placeholder="仓库" options={warehouseOptions} style={{ width: 160 }} />
          </Form.Item>
          <Form.Item name="status">
            <Select allowClear placeholder="状态" options={statusOptions} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="startDate">
            <Input placeholder="开始日期" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="endDate">
            <Input placeholder="结束日期" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                查询
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={saleList}
          loading={loading}
          scroll={{ x: 1300 }}
        />
      </Card>
      <Drawer
        title="销售单详情"
        width={720}
        open={Boolean(current)}
        onClose={() => setCurrent(null)}
      >
        {current ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="销售单号">{current.id}</Descriptions.Item>
              <Descriptions.Item label="客户">{current.customerName}</Descriptions.Item>
              <Descriptions.Item label="销售员">{current.sellerName}</Descriptions.Item>
              <Descriptions.Item label="出库仓库">{current.warehouseName}</Descriptions.Item>
              <Descriptions.Item label="销售日期">{current.orderDate}</Descriptions.Item>
              <Descriptions.Item label="销售金额">￥{current.totalAmount}</Descriptions.Item>
              <Descriptions.Item label="折扣率">{Number(current.discountRate || 0) * 100}%</Descriptions.Item>
              <Descriptions.Item label="实付金额">￥{current.paidAmount}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusColor[current.status] || "default"}>{current.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="备注">{current.remark || "-"}</Descriptions.Item>
            </Descriptions>
            <Table
              rowKey="id"
              title={() => "销售明细"}
              columns={detailColumns}
              dataSource={current.details || []}
              loading={detailLoading}
              pagination={false}
              size="small"
              scroll={{ x: 820 }}
            />
          </Space>
        ) : null}
      </Drawer>

      <Modal
        title="新建销售单"
        open={open}
        width={820}
        onCancel={() => {
          setOpen(false);
          form.resetFields();
          setSnList([]);
        }}
        onOk={handleSubmit}
        confirmLoading={saving}
        okText="提交给后端"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" initialValues={{ discountRate: 1, details: [{}] }}>
          <div className="form-grid">
            <Form.Item
              label="客户"
              name="customerId"
              rules={[{ required: true, message: "请选择客户" }]}
            >
              <Select placeholder="选择客户" options={customerOptions} />
            </Form.Item>
            <Form.Item
              label="销售员 ID"
              name="sellerId"
              rules={[{ required: true, message: "请填写销售员 ID" }]}
            >
              <InputNumber min={1} placeholder="例如 2" />
            </Form.Item>
            <Form.Item
              label="出库仓库"
              name="warehouseId"
              rules={[{ required: true, message: "请选择出库仓库" }]}
            >
              <Select
                placeholder="选择仓库"
                options={warehouseOptions}
                onChange={() => form.setFieldValue("details", [{}])}
              />
            </Form.Item>
            <Form.Item
              label="销售日期"
              name="orderDate"
              rules={[
                { required: true, message: "请输入销售日期" },
                {
                  pattern: /^\d{4}-\d{2}-\d{2}$/,
                  message: "日期格式应为 YYYY-MM-DD",
                },
              ]}
            >
              <Input placeholder="YYYY-MM-DD" />
            </Form.Item>
            <Form.Item
              label="折扣率"
              name="discountRate"
              rules={[{ required: true, message: "请输入折扣率" }]}
            >
              <InputNumber min={0} max={1} step={0.05} precision={2} />
            </Form.Item>
          </div>
          <Form.List name="details">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Card
                    key={field.key}
                    size="small"
                    className="detail-card"
                    title={`销售明细 ${field.name + 1}`}
                    extra={
                      fields.length > 1 ? (
                        <Button
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => remove(field.name)}
                        />
                      ) : null
                    }
                  >
                    <div className="form-grid">
                      <Form.Item
                        label="SN 码"
                        name={[field.name, "snCode"]}
                        rules={[{ required: true, message: "请选择 SN 码" }]}
                      >
                        <Select
                          showSearch
                          loading={snLoading}
                          options={snOptions}
                          placeholder="选择在库 SN 码"
                          optionFilterProp="label"
                        />
                      </Form.Item>
                      <Form.Item
                        label="销售单价"
                        name={[field.name, "unitPrice"]}
                        rules={[{ required: true, message: "请输入销售单价" }]}
                      >
                        <InputNumber min={0} precision={2} placeholder="单价" />
                      </Form.Item>
                    </div>
                  </Card>
                ))}
                <Button block icon={<PlusOutlined />} onClick={() => add()}>
                  添加销售明细
                </Button>
              </>
            )}
          </Form.List>
          <Form.Item label="备注" name="remark" className="form-item-top">
            <Input.TextArea rows={3} placeholder="销售备注" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
