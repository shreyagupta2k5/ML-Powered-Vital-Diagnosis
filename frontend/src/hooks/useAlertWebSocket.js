// ============================================================
// Custom Hook — useAlertWebSocket  (Phase 3 — Task 3.2)
// File: src/hooks/useAlertWebSocket.js
// 🔌 BACKEND CONNECT: WebSocket now active
// ✅ Alert Deduplication: skips repeat alerts for the same
//    patient within a 5-second debounce window
// ============================================================

import { useEffect, useRef } from "react";
import { useDispatch }       from "react-redux";
import { addAlert }          from "../store/alertsSlice";

const DEDUPE_WINDOW_MS = 5000; // 5-second debounce window

export default function useAlertWebSocket() {
  const dispatch       = useDispatch();
  const wsRef          = useRef(null);
  const retryCountRef  = useRef(0);
  const retryTimerRef  = useRef(null);

  // Tracks the last time we accepted an alert for each patient_id
  // e.g. { "PT-007": 1718999999999, "TEST_ALERT_001": 1718999991234 }
  const lastAlertTimeRef = useRef({});

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

        // ── DEDUPLICATION CHECK ──
        // Use patient_id as the key. System-wide alerts (no patient_id)
        // are grouped under "GLOBAL" so they get their own debounce.
        const dedupeKey = msg.patient_id || "GLOBAL";
        const now = Date.now();
        const lastTime = lastAlertTimeRef.current[dedupeKey];

        if (lastTime && now - lastTime < DEDUPE_WINDOW_MS) {
          console.log(`🔁 Duplicate alert suppressed for ${dedupeKey} (within ${DEDUPE_WINDOW_MS / 1000}s window)`);
          return; // skip — too soon since last alert for this patient
        }

        lastAlertTimeRef.current[dedupeKey] = now;

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

    return () => {
      clearTimeout(retryTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [dispatch]);
}