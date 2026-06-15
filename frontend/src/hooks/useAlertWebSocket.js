// ============================================================
// Custom Hook — useAlertWebSocket  (Phase 3 — Task 3.2)
// File: src/hooks/useAlertWebSocket.js
// 🔌 BACKEND CONNECT: WebSocket now active
// ============================================================

import { useEffect, useRef } from "react";
import { useDispatch }       from "react-redux";
import { addAlert }          from "../store/alertsSlice";

export default function useAlertWebSocket() {
  const dispatch       = useDispatch();
  const wsRef          = useRef(null);
  const retryCountRef  = useRef(0);
  const retryTimerRef  = useRef(null);

  function connect() {
    const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/alerts/broadcast`;
    console.log("🔌 Connecting to WebSocket:", wsUrl);
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log("✅ WebSocket connected to broadcast channel");
      retryCountRef.current = 0;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("📡 WebSocket message received:", msg);
        dispatch(addAlert({
          id:         Date.now(),
          type:       msg.type,
          patient_id: msg.patient_id,
          risk_score: msg.risk_score,
          timestamp:  msg.timestamp || new Date().toISOString(),
          read:       false,
        }));
      } catch (e) {
        console.error("Failed to parse WebSocket message", e);
      }
    };

    wsRef.current.onerror = (err) => {
      console.warn("WebSocket error", err);
    };

    wsRef.current.onclose = () => {
      // Exponential backoff: 2s, 4s, 8s, 16s, max 30s
      const delay = Math.min(2000 * Math.pow(2, retryCountRef.current), 30000);
      retryCountRef.current += 1;
      console.log(`WebSocket closed — reconnecting in ${delay / 1000}s`);
      retryTimerRef.current = setTimeout(connect, delay);
    };
  }

  useEffect(() => {
    connect();

    // Mock alerts removed — using real WebSocket now
    // const mockTimer = setInterval(() => { ... }, 30000);

    return () => {
      clearTimeout(retryTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [dispatch]);
}