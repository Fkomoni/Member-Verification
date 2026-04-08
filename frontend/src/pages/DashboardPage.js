import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import ScannerStatus from "../components/ScannerStatus";
import MemberSearch from "../components/MemberSearch";
import MemberCard from "../components/MemberCard";
import VisitTypeSelector from "../components/VisitTypeSelector";
import BiometricCapture from "../components/BiometricCapture";
import FingerprintValidation from "../components/FingerprintValidation";
import VerificationResult from "../components/VerificationResult";
import styles from "./DashboardPage.module.css";

export default function DashboardPage() {
  const { provider, logout } = useAuth();
  const [member, setMember] = useState(null);
  const [visitType, setVisitType] = useState(null);
  const [result, setResult] = useState(null);

  const resetFlow = () => {
    setMember(null);
    setVisitType(null);
    setResult(null);
  };

  return (
    <div className={styles.page}>
      {/* ── Header ─────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerLogo}>
            <svg viewBox="0 0 40 40" width="32" height="32">
              <circle cx="20" cy="20" r="18" fill="url(#hdrGrad)" />
              <defs>
                <linearGradient id="hdrGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F15A24" />
                  <stop offset="100%" stopColor="#FFCE07" />
                </linearGradient>
              </defs>
            </svg>
            <div>
              <span className={styles.headerBrand}>LEADWAY</span>
              <span className={styles.headerBrandHealth}> Health</span>
            </div>
          </div>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Verification Portal</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.providerName}>{provider?.provider_name}</span>
          <button onClick={logout} className={styles.logoutBtn}>
            Sign Out
          </button>
        </div>
      </header>

      {/* ── Main Content ───────────────────────────── */}
      <main className={styles.main}>
        <ScannerStatus />

        {/* Step 1: Search for member */}
        {!member && <MemberSearch onFound={setMember} />}

        {/* Steps 2-4: Member found, go through verification flow */}
        {member && !result && (
          <div className={styles.flowContainer}>
            <MemberCard member={member} />

            {/* If ineligible, show result immediately */}
            {member.verification_status === "INELIGIBLE" ? (
              <VerificationResult
                result={{
                  status: "ineligible",
                  message: member.verification_reason,
                  prognosis_data: member.prognosis_data,
                }}
                onReset={resetFlow}
              />
            ) : !visitType ? (
              /* Step 2: Select visit type */
              <VisitTypeSelector member={member} onSelect={setVisitType} />
            ) : !member.biometric_registered ? (
              /* Step 3a: Biometric capture (no fingerprint on file) */
              <BiometricCapture
                member={member}
                onComplete={(res) => {
                  setMember({ ...member, biometric_registered: true });
                  setResult({
                    status: "enrolled",
                    message: res.message,
                    visitType,
                  });
                }}
              />
            ) : (
              /* Step 3b: Fingerprint validation (has biometric on file) */
              <FingerprintValidation
                member={member}
                onResult={(res) =>
                  setResult({
                    status: res.verification_status?.toLowerCase() || (res.match ? "eligible" : "denied"),
                    message: res.message,
                    verificationToken: res.verification_token,
                    verificationReason: res.verification_reason,
                    prognosisData: res.prognosis_data,
                    visitType,
                  })
                }
              />
            )}
          </div>
        )}

        {/* Step 5: Show final result */}
        {result && <VerificationResult result={result} onReset={resetFlow} />}
      </main>
    </div>
  );
}
