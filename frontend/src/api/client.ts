import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 300000, // 5 min for SSE streaming
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: attach JWT
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
