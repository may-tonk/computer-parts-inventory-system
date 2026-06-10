import request from "./request";

export function getStockDetails(params) {
  return request.get("/stocks/detail", { params });
}

export function getSnList(params) {
  return request.get("/product-sn", { params });
}

export function getSnDetail(sn) {
  return request.get(`/product-sn/${sn}`);
}

export function getInventoryWarnings() {
  return request.get("/stocks/warnings");
}
