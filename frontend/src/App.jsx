// ============================================================
// App.jsx — Root Router
// Updated for Phase 2: ProtectedRoute now guards private pages
// ============================================================

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute      from "./components/auth/ProtectedRoute";
import LoginPage           from "./pages/Login.jsx";
import DashboardPage       from "./pages/Dashboard.jsx";
import PatientDetailPage   from "./pages/Patient.jsx";
import AdminPage           from "./pages/Admin.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route — no login needed */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes — ProtectedRoute redirects to /login if no token */}
        <Route path="/dashboard" element={
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />
        <Route path="/patient/:id" element={
          <ProtectedRoute><PatientDetailPage /></ProtectedRoute>
        } />
        <Route path="/admin/mlops" element={
          <ProtectedRoute><AdminPage /></ProtectedRoute>
        } />

        {/* Default — go to dashboard (ProtectedRoute will redirect to login if needed) */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
