import axios from "axios";
// import { mockAdapter } from "./mockServer";
import { getStoredToken, isGuestToken } from "../utils/storage";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 20000
  // baseURL: "/api",
  // adapter: mockAdapter,
});

const extractApiErrorMessage = (error) => {
  const data = error?.response?.data;
  if (!data) return error?.message || "Đã xảy ra lỗi";

  if (typeof data === "string") return data;
  if (typeof data.message === "string" && data.message.trim()) return data.message;
  if (typeof data.detail === "string" && data.detail.trim()) return data.detail;
  if (Array.isArray(data.detail) && data.detail.length) {
    const firstDetail = data.detail[0];
    if (typeof firstDetail === "string") return firstDetail;
    if (firstDetail?.msg) return firstDetail.msg;
    if (firstDetail?.message) return firstDetail.message;
  }

  return error?.message || "Đã xảy ra lỗi";
};

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token && !isGuestToken(token)) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(new Error(extractApiErrorMessage(error)))
);

export default apiClient;
