// 🔌 BACKEND CONNECT: uncomment when linking frontend to backend
// import api from "../config/api";

import { mockHealth } from "../mocks/mockHealth";
import { mockDrift } from "../mocks/mockDrift";

export const mlopsService = {
  getHealth: async () => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const response = await api.get("/health");
    // return response.data;

    // MOCK
    return mockHealth;
  },

  getDriftStatus: async (trackId) => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const response = await api.get(`/api/v1/drift/${trackId}`);
    // return response.data;

    // MOCK
    return mockDrift;
  },

  getActiveModel: async (trackId) => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const response = await api.get(`/api/v1/registry/${trackId}/active`);
    // return response.data;

    // MOCK
    return {
      track_id: trackId,
      model_version: "v2.1.0",
      training_date: "2026-05-15",
      auc: 0.91,
      f1: 0.87,
      recall: 0.89,
      deployment_status: "ACTIVE",
    };
  },
};