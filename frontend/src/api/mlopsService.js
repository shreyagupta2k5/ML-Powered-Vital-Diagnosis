import api from "../config/api";

export const mlopsService = {
  getHealth: async () => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.get("/health");
    return response.data;
  },

  getDriftStatus: async (trackId) => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.get(`/api/v1/drift/${trackId}`);
    return response.data;
  },

  getActiveModel: async (trackId) => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.get(`/api/v1/registry/${trackId}/active`);
    return response.data;
  },
};