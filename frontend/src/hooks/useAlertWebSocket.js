// ============================================================
// Custom Hook — useAlertWebSocket  (Phase 3 — Task 3.2)
// File: src/hooks/useAlertWebSocket.js
//
// WHAT THIS DOES:
//   - Creates a WebSocket connection to get live alerts
//   - Every new alert is added to Redux store (addAlert)
//   - Has automatic reconnect logic if connection drops
//   - Cleans up when component using it unmounts
//
// ⚠️ WebSocket connection is COMMENTED OUT (no backend yet)
//    Mock alerts fire every 30 seconds for demo purposes
// ============================================================

import { useEffect, useRef } from "react";
import { useDispatch }       from "react-redux";
import { addAlert }          from "../store/alertsSlice";

export default function useAlertWebSocket() {
  const dispatch       = useDispatch();
  const wsRef          = useRef(null);   // stores the WebSocket object
  const retryCountRef  = useRef(0);      // how many reconnect attempts
  const retryTimerRef  = useRef(null);   // timer for reconnect delay

  // 🔌 BACKEND CONNECT: uncomment this entire function when linking frontend to backend
  // function connect() {
  //   const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/alerts/broadcast`;
  //   wsRef.current = new WebSocket(wsUrl);
  //
  //   wsRef.current.onopen = () => {
  //     console.log("✅ WebSocket connected to broadcast channel");
  //     retryCountRef.current = 0; // reset retry counter on success
  //   };
  //
  //   wsRef.current.onmessage = (event) => {
  //     try {
  //       const msg = JSON.parse(event.data);
  //       // msg shape: { type, patient_id, risk_score, timestamp }
  //       dispatch(addAlert({
  //         id:         Date.now(),
  //         type:       msg.type,       // "HIGH_RISK" | "DRIFT_DETECTED" | "MODEL_UPDATED"
  //         patient_id: msg.patient_id,
  //         risk_score: msg.risk_score,
  //         timestamp:  msg.timestamp || new Date().toISOString(),
  //         read:       false,
  //       }));
  //     } catch (e) {
  //       console.error("Failed to parse WebSocket message", e);
  //     }
  //   };
  //
  //   wsRef.current.onerror = (err) => {
  //     console.warn("WebSocket error", err);
  //   };
  //
  //   wsRef.current.onclose = () => {
  //     // Exponential backoff: 2s, 4s, 8s, 16s, max 30s
  //     const delay = Math.min(2000 * Math.pow(2, retryCountRef.current), 30000);
  //     retryCountRef.current += 1;
  //     console.log(`WebSocket closed — reconnecting in ${delay / 1000}s`);
  //     retryTimerRef.current = setTimeout(connect, delay);
  //   };
  // }

  useEffect(() => {
    // 🔌 BACKEND CONNECT: replace this mock with connect() when backend is ready
    // connect();

    // ── MOCK: fire a fake alert every 30 seconds so we can test the UI ──
    const MOCK_ALERTS = [
      { type: "HIGH_RISK",       patient_id: "PT-007", risk_score: 0.85 },
      { type: "DRIFT_DETECTED",  patient_id: null,     risk_score: null },
      { type: "HIGH_RISK",       patient_id: "PT-003", risk_score: 0.67 },
      { type: "MODEL_UPDATED",   patient_id: null,     risk_score: null },
    ];
    let mockIndex = 0;

    const mockTimer = setInterval(() => {
      const alert = MOCK_ALERTS[mockIndex % MOCK_ALERTS.length];
      dispatch(addAlert({
        id:         Date.now(),
        type:       alert.type,
        patient_id: alert.patient_id,
        risk_score: alert.risk_score,
        timestamp:  new Date().toISOString(),
        read:       false,
      }));
      mockIndex++;
    }, 30000); // every 30 seconds

    // Cleanup on unmount
    return () => {
      clearInterval(mockTimer);
      clearTimeout(retryTimerRef.current);
      // 🔌 BACKEND CONNECT: also add ws.close() when backend is ready
      // if (wsRef.current) wsRef.current.close();
    };
  }, [dispatch]);
}
