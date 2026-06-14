// 🔌 BACKEND CONNECT: uncomment when linking frontend to backend
// import api from "../config/api";

import { mockPrediction } from "../mocks/mockPrediction";

export const predictionService = {
  predictEnsemble: async (payload) => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const response = await api.post("/api/v1/ensemble/predict", payload);
    // return response.data;

    // MOCK
    return mockPrediction;
  },

  predictTrack1: async (payload) => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const response = await api.post("/api/v1/track1/predict", payload);
    // return response.data;

    return mockPrediction.track_results.track1;
  },

  predictTrack2: async (payload) => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const response = await api.post("/api/v1/track2/predict", payload);
    // return response.data;

    return mockPrediction.track_results.track2;
  },

  predictTrack3: async (payload) => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const response = await api.post("/api/v1/track3/predict", payload);
    // return response.data;

    return mockPrediction.track_results.track3;
  },
};