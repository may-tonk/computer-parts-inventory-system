import request from "./request";

export function getPurchases(params) {
  return request.get("/purchase-orders", { params });
}

export function getPurchaseDetail(id) {
  return request.get(`/purchase-orders/${id}`);
}

export function createPurchase(data) {
  return request.post("/purchase-orders", data);
}

export function getSales(params) {
  return request.get("/sales-orders", { params });
}

export function getSaleDetail(id) {
  return request.get(`/sales-orders/${id}`);
}

export function createSale(data) {
  return request.post("/sales-orders", data);
}

export function returnSale(id) {
  return request.post(`/sales-orders/${id}/return`);
}
