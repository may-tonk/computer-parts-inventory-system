import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Select,
  Space,
  Table,
  Tag,
} from "antd";
import { PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { getBrands, getCategories } from "../api/masterData.js";
import {
  createProduct,
  getProductDetail,
  getProducts,
  updateProduct,
  updateProductStatus,
} from "../api/accessories.js";

function AttributeFields({ categoryId, categories }) {
  const categoryName = categories.find((item) => item.id === categoryId)?.name;

  if (categoryName === "CPU") {
    return (
      <div className="form-grid">
        <Form.Item label="核心数" name={["attributes", "cores"]}>
          <InputNumber min={1} placeholder="例如 14" />
        </Form.Item>
        <Form.Item label="线程数" name={["attributes", "threads"]}>
          <InputNumber min={1} placeholder="例如 20" />
        </Form.Item>
        <Form.Item label="基础频率" name={["attributes", "baseFrequency"]}>
          <Input placeholder="例如 3.5GHz" />
        </Form.Item>
        <Form.Item label="最大频率" name={["attributes", "maxFrequency"]}>
          <Input placeholder="例如 5.3GHz" />
        </Form.Item>
        <Form.Item label="插槽类型" name={["attributes", "socketType"]}>
          <Input placeholder="例如 LGA1700" />
        </Form.Item>
        <Form.Item label="TDP" name={["attributes", "tdp"]}>
          <Input placeholder="例如 125W" />
        </Form.Item>
      </div>
    );
  }

  if (categoryName === "内存条") {
    return (
      <div className="form-grid">
        <Form.Item label="容量" name={["attributes", "capacity"]}>
          <Input placeholder="例如 32GB" />
        </Form.Item>
        <Form.Item label="内存类型" name={["attributes", "memoryType"]}>
          <Select
            placeholder="选择类型"
            options={["DDR4", "DDR5"].map((value) => ({ label: value, value }))}
          />
        </Form.Item>
        <Form.Item label="频率" name={["attributes", "frequency"]}>
          <Input placeholder="例如 6000MHz" />
        </Form.Item>
        <Form.Item label="时序" name={["attributes", "timing"]}>
          <Input placeholder="例如 CL36" />
        </Form.Item>
      </div>
    );
  }

  if (categoryName === "硬盘") {
    return (
      <div className="form-grid">
        <Form.Item label="硬盘类型" name={["attributes", "diskType"]}>
          <Select
            placeholder="选择类型"
            options={["SSD", "HDD"].map((value) => ({ label: value, value }))}
          />
        </Form.Item>
        <Form.Item label="接口类型" name={["attributes", "interfaceType"]}>
          <Select
            placeholder="选择接口"
            options={["SATA", "NVMe"].map((value) => ({ label: value, value }))}
          />
        </Form.Item>
        <Form.Item label="容量" name={["attributes", "capacity"]}>
          <Input placeholder="例如 1TB" />
        </Form.Item>
        <Form.Item label="缓存" name={["attributes", "cacheSize"]}>
          <Input placeholder="例如 1024MB" />
        </Form.Item>
      </div>
    );
  }

  if (categoryName === "主板") {
    return (
      <div className="form-grid">
        <Form.Item label="芯片组" name={["attributes", "chipset"]}>
          <Input placeholder="例如 B760" />
        </Form.Item>
        <Form.Item label="CPU 插槽" name={["attributes", "socketType"]}>
          <Input placeholder="例如 LGA1700" />
        </Form.Item>
        <Form.Item label="板型" name={["attributes", "formFactor"]}>
          <Select
            placeholder="选择板型"
            options={["ATX", "M-ATX", "ITX"].map((value) => ({
              label: value,
              value,
            }))}
          />
        </Form.Item>
        <Form.Item label="内存插槽数" name={["attributes", "memorySlots"]}>
          <InputNumber min={1} placeholder="例如 4" />
        </Form.Item>
        <Form.Item label="最大内存容量" name={["attributes", "maxMemory"]}>
          <Input placeholder="例如 128GB" />
        </Form.Item>
      </div>
    );
  }

  return null;
}

export default function Accessories() {
  const [form] = Form.useForm();
  const [productList, setProductList] = useState([]);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [categoryId, setCategoryId] = useState();
  const [open, setOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [saving, setSaving] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const selectedCategoryId = Form.useWatch("categoryId", form);

  const categoryOptions = useMemo(
    () => categories.map((item) => ({ label: item.name, value: item.id })),
    [categories]
  );

  const brandOptions = useMemo(
    () => brands.map((item) => ({ label: item.name, value: item.id })),
    [brands]
  );

  useEffect(() => {
    async function loadOptions() {
      try {
        const [brandData, categoryData] = await Promise.all([
          getBrands(),
          getCategories(),
        ]);
        setBrands(brandData);
        setCategories(categoryData);
      } catch (error) {
        message.error(error.message);
      }
    }
    loadOptions();
  }, []);

  async function loadProducts() {
    setLoading(true);
    try {
      const data = await getProducts({
        keyword: keyword || undefined,
        categoryId: categoryId || undefined,
      });
      setProductList(data);
    } catch (error) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProducts();
  }, [keyword, categoryId]);

  function handleCreate() {
    setEditingProduct(null);
    form.resetFields();
    form.setFieldsValue({ status: "在售", warningValue: 0, attributes: {} });
    setOpen(true);
  }

  async function handleEdit(record) {
    setEditingProduct(record);
    setOpen(true);
    setDetailLoading(true);
    try {
      const data = await getProductDetail(record.id);
      form.setFieldsValue({
        name: data.name,
        categoryId: data.categoryId,
        brandId: data.brandId,
        model: data.model,
        purchasePrice: data.purchasePrice,
        salePrice: data.salePrice,
        warningValue: data.warningValue,
        status: data.status,
        remark: data.remark,
        attributes: data.attributes || {},
      });
    } catch (error) {
      message.error(error.message);
      setOpen(false);
      setEditingProduct(null);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleSave() {
    const values = await form.validateFields();
    setSaving(true);
    try {
      if (editingProduct) {
        await updateProduct(editingProduct.id, values);
        message.success("配件信息已更新");
      } else {
        await createProduct(values);
        message.success("配件已新增");
      }
      setOpen(false);
      setEditingProduct(null);
      form.resetFields();
      await loadProducts();
    } catch (error) {
      message.error(error.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleStatusToggle(record) {
    const nextStatus = record.status === "停用" ? "在售" : "停用";
    try {
      await updateProductStatus(record.id, nextStatus);
      message.success(`配件已${nextStatus === "停用" ? "停用" : "恢复"}`);
      await loadProducts();
    } catch (error) {
      message.error(error.message);
    }
  }

  const columns = [
    { title: "配件名称", dataIndex: "name", width: 220 },
    { title: "分类", dataIndex: "categoryName", render: (value) => <Tag>{value}</Tag> },
    { title: "品牌", dataIndex: "brandName" },
    { title: "规格型号", dataIndex: "model" },
    { title: "进价", dataIndex: "purchasePrice", render: (value) => `¥${value}` },
    { title: "售价", dataIndex: "salePrice", render: (value) => `¥${value}` },
    { title: "预警值", dataIndex: "warningValue" },
    { title: "当前库存", dataIndex: "stock" },
    {
      title: "状态",
      dataIndex: "status",
      render: (value) => (
        <Tag color={value === "停用" ? "default" : "green"}>{value}</Tag>
      ),
    },
    {
      title: "操作",
      fixed: "right",
      width: 150,
      render: (_, record) => {
        const actionText = record.status === "停用" ? "恢复" : "停用";
        return (
          <Space>
            <Button type="link" size="small" onClick={() => handleEdit(record)}>
              编辑
            </Button>
            <Button
              type="link"
              size="small"
              danger={record.status !== "停用"}
              onClick={() => handleStatusToggle(record)}
            >
              {actionText}
            </Button>
          </Space>
        );
      },
    },
  ];

  return (
    <>
      <PageHeader
        title="配件管理"
        description="对应 product 表和四类属性子表，新增时根据分类动态填写 CPU、内存、硬盘、主板参数。"
        action={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新增配件
          </Button>
        }
      />
      <Card>
        <Space wrap className="toolbar">
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="搜索名称 / 品牌 / 型号"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            style={{ width: 260 }}
          />
          <Select
            allowClear
            placeholder="分类"
            options={categoryOptions}
            value={categoryId}
            onChange={setCategoryId}
            style={{ width: 160 }}
          />
        </Space>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={productList}
          loading={loading}
          pagination={{ pageSize: 8 }}
          scroll={{ x: 1120 }}
        />
      </Card>

      <Modal
        title={editingProduct ? "编辑配件型号" : "新增配件型号"}
        open={open}
        width={760}
        onCancel={() => {
          setOpen(false);
          setEditingProduct(null);
          form.resetFields();
        }}
        onOk={handleSave}
        confirmLoading={saving}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          disabled={detailLoading}
          initialValues={{ status: "在售", warningValue: 0, attributes: {} }}
        >
          <div className="form-grid">
            <Form.Item
              label="配件名称"
              name="name"
              rules={[{ required: true, message: "请输入配件名称" }]}
            >
              <Input placeholder="例如 Intel Core i5-14600KF" />
            </Form.Item>
            <Form.Item
              label="分类"
              name="categoryId"
              rules={[{ required: true, message: "请选择分类" }]}
            >
              <Select options={categoryOptions} placeholder="选择分类" />
            </Form.Item>
            <Form.Item
              label="品牌"
              name="brandId"
              rules={[{ required: true, message: "请选择品牌" }]}
            >
              <Select options={brandOptions} placeholder="选择品牌" />
            </Form.Item>
            <Form.Item
              label="规格型号"
              name="model"
              rules={[{ required: true, message: "请输入规格型号" }]}
            >
              <Input placeholder="填写规格型号" />
            </Form.Item>
            <Form.Item label="进价" name="purchasePrice">
              <InputNumber min={0} precision={2} placeholder="采购进价" />
            </Form.Item>
            <Form.Item label="售价" name="salePrice">
              <InputNumber min={0} precision={2} placeholder="标准售价" />
            </Form.Item>
            <Form.Item label="库存预警值" name="warningValue">
              <InputNumber min={0} placeholder="低于该数量时预警" />
            </Form.Item>
            <Form.Item label="状态" name="status">
              <Select
                options={["在售", "停用"].map((value) => ({ label: value, value }))}
              />
            </Form.Item>
          </div>
          <AttributeFields categoryId={selectedCategoryId} categories={categories} />
          <Form.Item label="备注" name="remark">
            <Input.TextArea rows={3} placeholder="补充说明" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
