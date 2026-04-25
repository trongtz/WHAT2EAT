import axios from "axios";
import { mockAdapter } from "./mockServer";
import { getStoredToken } from "../utils/storage";

const apiClient = axios.create({
  baseURL: "/api",
  adapter: mockAdapter,
});

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(new Error(error.response?.data?.message || error.message || "Đã xảy ra lỗi"))
);

export default apiClient;
