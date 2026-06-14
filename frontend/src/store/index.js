import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./authSlice";
import alertsReducer from "./alertsSlice";
import patientsReducer from "./patientsSlice";

// 🔌 BACKEND CONNECT: uncomment redux-persist when linking
// import { persistStore, persistReducer } from "redux-persist";
// import storage from "redux-persist/lib/storage";
// import { combineReducers } from "@reduxjs/toolkit";
// const persistConfig = { key: "root", storage, whitelist: ["auth"] };

const store = configureStore({
  reducer: {
    auth: authReducer,
    alerts: alertsReducer,
    patients: patientsReducer,
  },
});

export default store;