import request from "./request";

export function getProducts(params) {
  return request.get("/products", { params });
}

export function getProductDetail(id) {
  return request.get(`/products/${id}`);
}

export function createProduct(data) {
  return request.post("/products", data);
}

export function updateProduct(id, data) {
  return request.put(`/products/${id}`, data);
}

export function updateProductStatus(id, status) {
  return request.put(`/products/${id}/status`, { status });
}

export function updateProductWarningValue(id, warningValue) {
  return request.put(`/products/${id}/warning-value`, { warningValue });
}

export function deleteProduct(id) {
  return request.delete(`/products/${id}`);
}
