import React, { useState } from "react";
import { useAgentAuth } from "../context/AgentAuthContext";
import AuthCodeGenerator from "../components/AuthCodeGenerator";
import AuthCodeResult from "../components/AuthCodeResult";
import CodeHistory from "../components/CodeHistory";
import styles from "./CallCenterDashboardPage.module.css";

export default function CallCenterDashboardPage() {
  const { agent, logout } = useAgentAuth();
  const [generatedCode, setGeneratedCode] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCodeGenerated = (codeData) => {
    setGeneratedCode(codeData);
    setRefreshKey((k) => k + 1);
  };

  const handleDismissResult = () => {
    setGeneratedCode(null);
  };

  return (
    <div className={styles.page}>
      {/* -- Header ------------------------------------ */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerLogo}>
            <img src="/leadway-logo.png" alt="Leadway Health HMO" style={{ height: 36, width: "auto" }} />
          </div>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Call Center Portal</span>
        </div>
        <div className={styles.headerRight}>
          <div className={styles.agentInfo}>
            <span className={styles.agentName}>{agent?.agent_name}</span>
            <span className={styles.agentRole}>
              {agent?.role === "call_center"
                ? "Call Center Agent"
                : agent?.role === "admin"
                ? "Administrator"
                : agent?.role}
            </span>
          </div>
          <button onClick={logout} className={styles.logoutBtn}>
            Sign Out
          </button>
        </div>
      </header>

      {/* -- Main Content -------------------------------- */}
      <main className={styles.main}>
        <div className={styles.welcomeBar}>
          <h1 className={styles.welcomeTitle}>Authorization Code Management</h1>
          <p className={styles.welcomeSubtitle}>
            Generate and manage authorization codes for member reimbursement claims
          </p>
        </div>

        <div className={styles.content}>
          {generatedCode ? (
            <AuthCodeResult
              codeData={generatedCode}
              onDismiss={handleDismissResult}
            />
          ) : (
            <AuthCodeGenerator onCodeGenerated={handleCodeGenerated} />
          )}

          <CodeHistory refreshKey={refreshKey} />
        </div>
      </main>
    </div>
  );
}
