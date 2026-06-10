import axios from "axios";

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api",
  timeout: 10000,
});

request.interceptors.response.use(
  (response) => {
    const payload = response.data;
    if (payload && typeof payload === "object" && "code" in payload) {
      if (payload.code >= 200 && payload.code < 300) {
        return payload.data;
      }
      return Promise.reject(new Error(payload.message || "接口请求失败"));
    }
    return payload;
  },
  (error) => {
    const message =
      error.response?.data?.message || error.message || "接口请求失败";
    return Promise.reject(new Error(message));
  }
);

export default request;
