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
import { getProducts } from "../api/accessories.js";
import { getSuppliers, getWarehouses } from "../api/masterData.js";
import { createPurchase, getPurchaseDetail, getPurchases } from "../api/orders.js";

export default function Purchases() {
  const [form] = Form.useForm();
  const [filterForm] = Form.useForm();
  const [current, setCurrent] = useState(null);
  const [open, setOpen] = useState(false);
  const [purchaseList, setPurchaseList] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const productOptions = useMemo(
    () =>
      products.map((item) => ({
        label: `${item.name} / ${item.model}`,
        value: item.id,
      })),
    [products]
  );

  const supplierOptions = useMemo(
    () => suppliers.map((item) => ({ label: item.name, value: item.id })),
    [suppliers]
  );

  const warehouseOptions = useMemo(
    () => warehouses.map((item) => ({ label: item.name, value: item.id })),
    [warehouses]
  );

  async function loadPurchases(params = filterForm.getFieldsValue()) {
    setLoading(true);
    try {
      const data = await getPurchases(params);
      setPurchaseList(data);
    } catch (error) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPurchases({});
  }, []);

  useEffect(() => {
    async function loadOptions() {
      try {
        const [supplierData, warehouseData, productData] = await Promise.all([
          getSuppliers(),
          getWarehouses(),
          getProducts({ status: "在售" }),
        ]);
        setSuppliers(supplierData);
        setWarehouses(warehouseData);
        setProducts(productData);
      } catch (error) {
        message.error(error.message);
      }
    }
    loadOptions();
  }, []);

  async function handleSearch() {
    await loadPurchases(filterForm.getFieldsValue());
  }

  async function handleReset() {
    filterForm.resetFields();
    await loadPurchases({});
  }

  async function handleView(record) {
    setCurrent(record);
    setDetailLoading(true);
    try {
      const data = await getPurchaseDetail(record.id);
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
      const result = await createPurchase(values);
      message.success(`采购入库成功，生成 ${result.generatedSnCodes.length} 个 SN`);
      setOpen(false);
      form.resetFields();
      await loadPurchases();
    } catch (error) {
      message.error(error.message);
    } finally {
      setSaving(false);
    }
  }

  const columns = [
    { title: "采购单号", dataIndex: "id", width: 160 },
    { title: "供应商", dataIndex: "supplierName" },
    { title: "采购员", dataIndex: "buyerName" },
    { title: "仓库", dataIndex: "warehouseName" },
    { title: "采购日期", dataIndex: "orderDate" },
    { title: "总金额", dataIndex: "totalAmount", render: (value) => `￥${value}` },
    { title: "状态", dataIndex: "status", render: (value) => <Tag color="green">{value}</Tag> },
    {
      title: "操作",
      render: (_, record) => (
        <Button type="link" onClick={() => handleView(record)}>
          查看
        </Button>
      ),
    },
  ];

  const detailColumns = [
    { title: "配件", dataIndex: "productName" },
    { title: "分类", dataIndex: "categoryName", width: 90 },
    { title: "品牌", dataIndex: "brandName", width: 110 },
    { title: "数量", dataIndex: "quantity", width: 80 },
    { title: "单价", dataIndex: "unitPrice", width: 100, render: (value) => `￥${value}` },
    { title: "小计", dataIndex: "subtotal", width: 100, render: (value) => `￥${value}` },
    { title: "批次号", dataIndex: "batchNo", width: 130, render: (value) => value || "-" },
  ];

  const snColumns = [
    { title: "SN 码", dataIndex: "snCode", width: 210 },
    { title: "配件", dataIndex: "productName" },
    { title: "批次号", dataIndex: "batchNo", width: 130, render: (value) => value || "-" },
    { title: "入库单号", dataIndex: "inboundNo", width: 160 },
    { title: "状态", dataIndex: "status", width: 90, render: (value) => <Tag>{value}</Tag> },
  ];

  return (
    <>
      <PageHeader
        title="采购管理"
        description="对应 purchase_order、purchase_detail、inbound_order、inbound_detail。前端提交采购单，后端事务生成入库记录和 SN。"
        action={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            新建采购单
          </Button>
        }
      />
      <Card>
        <Form form={filterForm} layout="inline" className="toolbar">
          <Form.Item name="keyword">
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="采购单号 / 供应商"
              style={{ width: 220 }}
            />
          </Form.Item>
          <Form.Item name="supplierId">
            <Select allowClear placeholder="供应商" options={supplierOptions} style={{ width: 180 }} />
          </Form.Item>
          <Form.Item name="buyerId">
            <InputNumber min={1} placeholder="采购员 ID" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="warehouseId">
            <Select allowClear placeholder="仓库" options={warehouseOptions} style={{ width: 160 }} />
          </Form.Item>
          <Form.Item name="status">
            <Select
              allowClear
              placeholder="状态"
              options={[{ label: "已完成", value: "已完成" }]}
              style={{ width: 120 }}
            />
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
          dataSource={purchaseList}
          loading={loading}
          scroll={{ x: 1180 }}
        />
      </Card>
      <Drawer
        title="采购单详情"
        width={720}
        open={Boolean(current)}
        onClose={() => setCurrent(null)}
      >
        {current ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="采购单号">{current.id}</Descriptions.Item>
              <Descriptions.Item label="供应商">{current.supplierName}</Descriptions.Item>
              <Descriptions.Item label="采购员">{current.buyerName}</Descriptions.Item>
              <Descriptions.Item label="入库仓库">{current.warehouseName}</Descriptions.Item>
              <Descriptions.Item label="采购日期">{current.orderDate}</Descriptions.Item>
              <Descriptions.Item label="总金额">￥{current.totalAmount}</Descriptions.Item>
              <Descriptions.Item label="状态">{current.status}</Descriptions.Item>
              <Descriptions.Item label="备注">{current.remark || "-"}</Descriptions.Item>
            </Descriptions>
            <Table
              rowKey="id"
              title={() => "采购明细"}
              columns={detailColumns}
              dataSource={current.details || []}
              loading={detailLoading}
              pagination={false}
              size="small"
              scroll={{ x: 760 }}
            />
            <Table
              rowKey="snCode"
              title={() => "本次入库 SN"}
              columns={snColumns}
              dataSource={current.snCodes || []}
              loading={detailLoading}
              pagination={{ pageSize: 6 }}
              size="small"
              scroll={{ x: 820 }}
            />
          </Space>
        ) : null}
      </Drawer>

      <Modal
        title="新建采购单"
        open={open}
        width={860}
        onCancel={() => {
          setOpen(false);
          form.resetFields();
        }}
        onOk={handleSubmit}
        confirmLoading={saving}
        okText="提交给后端"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" initialValues={{ details: [{}] }}>
          <div className="form-grid">
            <Form.Item
              label="供应商"
              name="supplierId"
              rules={[{ required: true, message: "请选择供应商" }]}
            >
              <Select placeholder="选择供应商" options={supplierOptions} />
            </Form.Item>
            <Form.Item
              label="采购员 ID"
              name="buyerId"
              rules={[{ required: true, message: "请填写采购员 ID" }]}
            >
              <InputNumber min={1} placeholder="例如 1" />
            </Form.Item>
            <Form.Item
              label="入库仓库"
              name="warehouseId"
              rules={[{ required: true, message: "请选择入库仓库" }]}
            >
              <Select placeholder="选择仓库" options={warehouseOptions} />
            </Form.Item>
            <Form.Item
              label="采购日期"
              name="orderDate"
              rules={[
                { required: true, message: "请输入采购日期" },
                {
                  pattern: /^\d{4}-\d{2}-\d{2}$/,
                  message: "日期格式应为 YYYY-MM-DD",
                },
              ]}
            >
              <Input placeholder="YYYY-MM-DD" />
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
                    title={`采购明细 ${field.name + 1}`}
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
                        label="配件"
                        name={[field.name, "productId"]}
                        rules={[{ required: true, message: "请选择配件" }]}
                      >
                        <Select options={productOptions} placeholder="选择配件" />
                      </Form.Item>
                      <Form.Item
                        label="采购数量"
                        name={[field.name, "quantity"]}
                        rules={[{ required: true, message: "请输入采购数量" }]}
                      >
                        <InputNumber min={1} placeholder="数量" />
                      </Form.Item>
                      <Form.Item
                        label="采购单价"
                        name={[field.name, "unitPrice"]}
                        rules={[{ required: true, message: "请输入采购单价" }]}
                      >
                        <InputNumber min={0} precision={2} placeholder="单价" />
                      </Form.Item>
                      <Form.Item label="批次号" name={[field.name, "batchNo"]}>
                        <Input placeholder="例如 B20260607" />
                      </Form.Item>
                      <Form.Item
                        label="生产日期"
                        name={[field.name, "productionDate"]}
                        rules={[
                          {
                            pattern: /^\d{4}-\d{2}-\d{2}$/,
                            message: "日期格式应为 YYYY-MM-DD",
                          },
                        ]}
                      >
                        <Input placeholder="YYYY-MM-DD" />
                      </Form.Item>
                    </div>
                  </Card>
                ))}
                <Button block icon={<PlusOutlined />} onClick={() => add()}>
                  添加采购明细
                </Button>
              </>
            )}
          </Form.List>
          <Form.Item label="备注" name="remark" className="form-item-top">
            <Input.TextArea rows={3} placeholder="采购备注" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
