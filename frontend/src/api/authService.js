// 🔌 BACKEND CONNECT: uncomment when linking frontend to backend
// import api from "../config/api";

export const authService = {
  login: async (username, password) => {
    // 🔌 BACKEND CONNECT: uncomment when linking
    // const formData = new URLSearchParams();
    // formData.append("username", username);
    // formData.append("password", password);
    // const response = await api.post("/auth/token", formData, {
    //   headers: { "Content-Type": "application/x-www-form-urlencoded" },
    // });
    // return response.data;

    // MOCK: simulate successful login
    return {
      access_token: "mock_jwt_token_123",
      username: username,
    };
  },

  logout: () => {
    localStorage.removeItem("access_token");
  },
};