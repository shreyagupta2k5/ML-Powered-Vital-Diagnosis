import axios from "axios";

// Base axios instance — all API calls go through this
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// 🔌 BACKEND CONNECT: uncomment when linking frontend to backend

// // REQUEST INTERCEPTOR — auto-attach Bearer token to every request
// api.interceptors.request.use(
//   (config) => {
//     const token = localStorage.getItem("access_token");
//     if (token) {
//       config.headers.Authorization = `Bearer ${token}`;
//     }
//     return config;
//   },
//   (error) => Promise.reject(error)
// );

// // RESPONSE INTERCEPTOR — handle 401, 429, 502 globally
// api.interceptors.response.use(
//   (response) => response,
//   async (error) => {
//     const status = error?.response?.status;

//     // 401 — token expired or invalid, force logout
//     if (status === 401) {
//       localStorage.removeItem("access_token");
//       window.location.href = "/login";
//     }

//     // 429 — rate limited, retry after delay
//     if (status === 429) {
//       const retryAfter = error.response.headers["retry-after"] || 2;
//       await new Promise((res) => setTimeout(res, retryAfter * 1000));
//       return api.request(error.config);
//     }

//     // 502 — backend down, dispatch service degraded banner
//     if (status === 502) {
//       window.dispatchEvent(new CustomEvent("service-degraded"));
//     }

//     return Promise.reject(error);
//   }
// );

export default api;