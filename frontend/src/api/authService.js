import api from "../config/api";

export const authService = {
  login: async (username, password) => {
    // 🔌 BACKEND CONNECT: active
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    const response = await api.post("/auth/token", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return {
      access_token: response.data.access_token,
      username: username,
    };

    // MOCK: simulate successful login
    // return {
    //   access_token: "mock_jwt_token_123",
    //   username: username,
    // };
  },

  logout: () => {
    localStorage.removeItem("access_token");
  },
};