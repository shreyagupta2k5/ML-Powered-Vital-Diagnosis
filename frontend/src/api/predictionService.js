import api from "../config/api";

export const predictionService = {
  getHistory: async () => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.get("/api/v1/history");
    return response.data;
  },

  getPatientById: async (patientId) => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.get("/api/v1/history");
    const all = response.data;
    const patient = all.find(p => p.patient_id === patientId);
    return patient || null;
  },

  predictEnsemble: async (payload) => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.post("/api/v1/ensemble/predict", payload);
    return response.data;
    // MOCK
    // return mockPrediction;
  },

  predictTrack1: async (payload) => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.post("/api/v1/ensemble/predict/track1", payload);
    return response.data;
  },

  predictTrack2: async (payload) => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.post("/api/v1/ensemble/predict/track2", payload);
    return response.data;
  },

  predictTrack3: async (payload) => {
    // 🔌 BACKEND CONNECT: active
    const response = await api.post("/api/v1/ensemble/predict/track3", payload);
    return response.data;
  },
};