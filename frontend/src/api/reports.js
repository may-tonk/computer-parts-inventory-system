import request from "./request";

export function getSalesReport(params) {
  return request.get("/reports/sales", { params });
}

export function getDashboardSummary() {
  return request.get("/dashboard/summary");
}

export function getReportOverview(params) {
  return request.get("/reports/overview", { params });
}
