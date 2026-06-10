export const categories = [
  { id: 1, name: "CPU" },
  { id: 2, name: "内存条" },
  { id: 3, name: "硬盘" },
  { id: 4, name: "主板" },
];

export const brands = [
  { id: 1, name: "Intel" },
  { id: 2, name: "AMD" },
  { id: 3, name: "金百达" },
  { id: 4, name: "Samsung" },
  { id: 5, name: "ASUS" },
  { id: 6, name: "MSI" },
];

export const suppliers = [
  { id: 1, name: "华北数码批发中心", contact: "张经理", phone: "13800000000" },
  { id: 2, name: "深圳配件供应链", contact: "陈经理", phone: "13900000000" },
];

export const customers = [
  { id: 1, name: "星火电脑门店", contact: "李先生", phone: "13700000000", level: "VIP" },
  { id: 2, name: "个人客户-王同学", contact: "王同学", phone: "13600000000", level: "普通" },
];

export const warehouses = [
  { id: 1, name: "一号仓", manager: "仓管员A" },
  { id: 2, name: "二号仓", manager: "仓管员B" },
];

export const products = [
  {
    id: 1,
    name: "Intel Core i5-14600KF",
    categoryId: 1,
    categoryName: "CPU",
    brandId: 1,
    brandName: "Intel",
    model: "i5-14600KF",
    purchasePrice: 1580,
    salePrice: 1899,
    warningValue: 8,
    stock: 18,
    status: "在售",
    attributes: {
      cores: 14,
      threads: 20,
      baseFrequency: "3.5GHz",
      maxFrequency: "5.3GHz",
      socketType: "LGA1700",
      tdp: "125W",
    },
  },
  {
    id: 2,
    name: "AMD Ryzen 7 7800X3D",
    categoryId: 1,
    categoryName: "CPU",
    brandId: 2,
    brandName: "AMD",
    model: "7800X3D",
    purchasePrice: 2480,
    salePrice: 2899,
    warningValue: 6,
    stock: 9,
    status: "在售",
    attributes: {
      cores: 8,
      threads: 16,
      baseFrequency: "4.2GHz",
      maxFrequency: "5.0GHz",
      socketType: "AM5",
      tdp: "120W",
    },
  },
  {
    id: 3,
    name: "KingBank DDR5 32GB",
    categoryId: 2,
    categoryName: "内存条",
    brandId: 3,
    brandName: "金百达",
    model: "DDR5 6000 32GB",
    purchasePrice: 560,
    salePrice: 699,
    warningValue: 12,
    stock: 31,
    status: "在售",
    attributes: {
      capacity: "32GB",
      memoryType: "DDR5",
      frequency: "6000MHz",
      timing: "CL36",
    },
  },
  {
    id: 4,
    name: "Samsung 990 PRO 1TB",
    categoryId: 3,
    categoryName: "硬盘",
    brandId: 4,
    brandName: "Samsung",
    model: "NVMe 1TB",
    purchasePrice: 690,
    salePrice: 899,
    warningValue: 10,
    stock: 7,
    status: "在售",
    attributes: {
      diskType: "SSD",
      interfaceType: "NVMe",
      capacity: "1TB",
      cache: "1024MB",
    },
  },
  {
    id: 5,
    name: "ASUS TUF B760M-PLUS",
    categoryId: 4,
    categoryName: "主板",
    brandId: 5,
    brandName: "ASUS",
    model: "B760M-PLUS",
    purchasePrice: 820,
    salePrice: 999,
    warningValue: 6,
    stock: 14,
    status: "在售",
    attributes: {
      chipset: "B760",
      socketType: "LGA1700",
      formFactor: "M-ATX",
      memorySlots: 4,
      maxMemory: "128GB",
    },
  },
];

export const stockDetails = products.map((item, index) => ({
  id: item.id,
  productId: item.id,
  productName: item.name,
  categoryName: item.categoryName,
  brandName: item.brandName,
  warehouseId: index % 2 === 0 ? 1 : 2,
  warehouseName: index % 2 === 0 ? "一号仓" : "二号仓",
  quantity: item.stock,
  warningValue: item.warningValue,
  status: item.stock <= item.warningValue ? "低库存" : "正常",
  updatedAt: "2026-06-07 10:00:00",
}));

export const productSnList = [
  {
    id: 1,
    snCode: "CPU-INTEL-20260601-0001",
    productId: 1,
    productName: "Intel Core i5-14600KF",
    categoryName: "CPU",
    brandName: "Intel",
    warehouseName: "一号仓",
    batchNo: "B20260601",
    status: "在库",
    inboundDate: "2026-06-01",
    warrantyEndDate: "2029-06-01",
  },
  {
    id: 2,
    snCode: "SSD-SAMSUNG-20260602-0007",
    productId: 4,
    productName: "Samsung 990 PRO 1TB",
    categoryName: "硬盘",
    brandName: "Samsung",
    warehouseName: "二号仓",
    batchNo: "B20260602",
    status: "在库",
    inboundDate: "2026-06-02",
    warrantyEndDate: "2028-06-02",
  },
  {
    id: 3,
    snCode: "MB-ASUS-20260603-0012",
    productId: 5,
    productName: "ASUS TUF B760M-PLUS",
    categoryName: "主板",
    brandName: "ASUS",
    warehouseName: "一号仓",
    batchNo: "B20260603",
    status: "锁定",
    inboundDate: "2026-06-03",
    warrantyEndDate: "2029-06-03",
  },
];

export const inventoryWarnings = stockDetails.filter(
  (item) => item.quantity <= item.warningValue
);

export const purchases = [
  {
    id: "PO20260601001",
    supplierId: 1,
    supplierName: "华北数码批发中心",
    buyerId: 1,
    buyerName: "采购员A",
    warehouseId: 1,
    warehouseName: "一号仓",
    orderDate: "2026-06-01",
    totalAmount: 34800,
    status: "已完成",
    remark: "第一批采购入库",
  },
  {
    id: "PO20260602001",
    supplierId: 2,
    supplierName: "深圳配件供应链",
    buyerId: 2,
    buyerName: "采购员B",
    warehouseId: 2,
    warehouseName: "二号仓",
    orderDate: "2026-06-02",
    totalAmount: 21600,
    status: "已完成",
    remark: "第二批采购入库",
  },
];

export const sales = [
  {
    id: "SO20260603001",
    customerId: 1,
    customerName: "星火电脑门店",
    sellerId: 2,
    sellerName: "销售员A",
    warehouseId: 1,
    warehouseName: "一号仓",
    orderDate: "2026-06-03",
    totalAmount: 12880,
    discountRate: 0.95,
    paidAmount: 12236,
    status: "已完成",
    remark: "门店客户销售",
  },
  {
    id: "SO20260604001",
    customerId: 2,
    customerName: "个人客户-王同学",
    sellerId: 3,
    sellerName: "销售员B",
    warehouseId: 1,
    warehouseName: "一号仓",
    orderDate: "2026-06-04",
    totalAmount: 5397,
    discountRate: 1,
    paidAmount: 5397,
    status: "已完成",
    remark: "个人客户销售",
  },
];

export const salesTrend = [
  { date: "6/1", salesAmount: 6800, salesQuantity: 4 },
  { date: "6/2", salesAmount: 9600, salesQuantity: 6 },
  { date: "6/3", salesAmount: 12880, salesQuantity: 8 },
  { date: "6/4", salesAmount: 5397, salesQuantity: 3 },
  { date: "6/5", salesAmount: 15860, salesQuantity: 9 },
];
