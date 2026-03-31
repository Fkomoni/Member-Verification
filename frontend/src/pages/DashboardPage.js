import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import ScannerStatus from "../components/ScannerStatus";
import MemberSearch from "../components/MemberSearch";
import MemberCard from "../components/MemberCard";
import BiometricCapture from "../components/BiometricCapture";
import FingerprintValidation from "../components/FingerprintValidation";
import VerificationResult from "../components/VerificationResult";
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
      <header className={styles.header}>
        <div>
          <h1 className={styles.logo}>Verification Portal</h1>
          <span className={styles.providerName}>{provider?.provider_name}</span>
        </div>
        <button onClick={logout} className={styles.logoutBtn}>
          Logout
        </button>
      </header>

      <main className={styles.main}>
        <ScannerStatus />

        {/* Step 1: Search member */}
        {!member && <MemberSearch onFound={setMember} />}

        {/* Step 2: Show member info + appropriate action */}
        {member && !result && (
          <div className={styles.flowContainer}>
            <MemberCard member={member} />

            {!member.biometric_registered ? (
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
                    status: res.match ? "approved" : "denied",
                    message: res.message,
                    verificationToken: res.verification_token,
                  })
                }
              />
            )}
          </div>
        )}

        {/* Step 3: Show result */}
        {result && (
          <VerificationResult result={result} onReset={resetFlow} />
        )}
      </main>
    </div>
  );
}
