// ============================================================
// ProtectedRoute  (Phase 2 — Task 2.1)
// File: src/components/auth/ProtectedRoute.jsx
//
// WHAT THIS DOES:
//   Wraps any page that needs login.
//   If user has no token → sends them to /login
//   If user has token    → shows the page normally
//
// HOW TO USE:
//   <Route path="/dashboard" element={
//     <ProtectedRoute><DashboardPage /></ProtectedRoute>
//   } />
// ============================================================

import { useSelector } from "react-redux";
import { Navigate }    from "react-router-dom";

export default function ProtectedRoute({ children }) {
  // Check Redux store first
  const isAuthenticated = useSelector((s) => s.auth.isAuthenticated);

  // Also check localStorage (in case page was refreshed)
  const tokenInStorage = localStorage.getItem("access_token");

  if (!isAuthenticated && !tokenInStorage) {
    // Not logged in → send to login page
    return <Navigate to="/login" replace />;
  }

  // Logged in → show the actual page
  return children;
}
