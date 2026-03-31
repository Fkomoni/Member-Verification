import React, { useEffect, useState } from "react";
import { getDeviceStatus } from "../services/fingerprintBridge";
import styles from "./shared.module.css";

export default function ScannerStatus() {
  const [status, setStatus] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      setChecking(true);
      const result = await getDeviceStatus();
      if (!cancelled) {
        setStatus(result);
        setChecking(false);
      }
    }
    check();
    // Re-check every 10 seconds
    const interval = setInterval(check, 10000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (checking && !status) return null;

  const connected = status?.connected;

  return (
    <div className={connected ? styles.scannerConnected : styles.scannerDisconnected}>
      <span className={styles.scannerDot} />
      <span className={styles.scannerText}>
        {connected
          ? `FS80H Connected${status.deviceInfo?.lfdSupported ? " (LFD Active)" : ""}`
          : "FS80H Scanner Not Detected"}
      </span>
    </div>
  );
}
