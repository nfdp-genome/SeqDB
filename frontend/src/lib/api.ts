import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  // Ensure trailing slash on paths that don't have a file extension or query,
  // so FastAPI doesn't 307-redirect and drop the POST body.
  if (config.url && !config.url.endsWith("/") && !config.url.includes("?") && !config.url.match(/\.\w+$/)) {
    config.url = config.url + "/";
  }

  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
