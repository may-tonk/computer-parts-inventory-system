import request from "./request";

export function getBrands() {
  return request.get("/brands");
}

export function getCategories() {
  return request.get("/categories");
}

export function getSuppliers() {
  return request.get("/suppliers");
}

export function getCustomers() {
  return request.get("/customers");
}

export function getWarehouses() {
  return request.get("/warehouses");
}
