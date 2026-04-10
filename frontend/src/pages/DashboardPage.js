import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import ScannerStatus from "../components/ScannerStatus";
import MemberSearch from "../components/MemberSearch";
import MemberCard from "../components/MemberCard";
import BiometricCapture from "../components/BiometricCapture";
import FingerprintValidation from "../components/FingerprintValidation";
import VerificationResult from "../components/VerificationResult";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./DashboardPage.module.css";

export default function DashboardPage() {
  const { provider, logout } = useAuth();
  const [member, setMember] = useState(null);
  const [result, setResult] = useState(null);

  const resetFlow = () => {
    setMember(null);
    setResult(null);
  };

  return (
    <div className={styles.page}>
      {/* ── Header ─────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <Link to="/dashboard" className={styles.headerLogo}>
            <img src={logo} alt="Leadway Health" className={styles.headerLogoImg} />
          </Link>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Provider Portal</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.providerName}>{provider?.provider_name}</span>
          <button onClick={logout} className={styles.logoutBtn}>
            Sign Out
          </button>
        </div>
      </header>

      {/* ── Navigation ─────────────────────────────── */}
      <nav className={styles.navBar}>
        <Link to="/dashboard" className={styles.navLinkActive}>Verification</Link>
        <Link to="/medication-request" className={styles.navLink}>New Rx Request</Link>
        <Link to="/medication-requests" className={styles.navLink}>Request History</Link>
      </nav>

      {/* ── Main Content ───────────────────────────── */}
      <main className={styles.main}>
        <ScannerStatus />

        {!member && <MemberSearch onFound={setMember} />}

        {member && !result && (
          <div className={styles.flowContainer}>
            <MemberCard member={member} />

            {member.verification_status === "INELIGIBLE" ? (
              <VerificationResult
                result={{
                  status: "ineligible",
                  message: member.verification_reason,
                  prognosis_data: member.prognosis_data,
                }}
                onReset={resetFlow}
              />
            ) : !member.biometric_registered ? (
              <BiometricCapture
                member={member}
                onComplete={(res) => {
                  setMember({ ...member, biometric_registered: true });
                  setResult({
                    status: "enrolled",
                    message: res.message,
                  });
                }}
              />
            ) : (
              <FingerprintValidation
                member={member}
                onResult={(res) =>
                  setResult({
                    status: res.verification_status?.toLowerCase() || (res.match ? "eligible" : "denied"),
                    message: res.message,
                    verificationToken: res.verification_token,
                    verificationReason: res.verification_reason,
                    prognosisData: res.prognosis_data,
                  })
                }
              />
            )}
          </div>
        )}

        {result && <VerificationResult result={result} onReset={resetFlow} />}
      </main>
    </div>
  );
}
