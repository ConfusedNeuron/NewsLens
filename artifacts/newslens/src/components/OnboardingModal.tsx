import { useState } from "react";
import { UserProfile } from "./NewsCard";

interface OnboardingModalProps {
  onComplete: (profile: UserProfile) => void;
  onDismiss: () => void;
}

// Options now live in one shared module so this modal and the /profile page cannot
// drift apart again. See src/lib/profile-vocab.ts for the history.
import {
  INCOME_OPTIONS,
  SECTOR_OPTIONS,
  INVESTMENT_OPTIONS,
  CITY_OPTIONS,
} from "@/lib/profile-vocab";

const STEPS = 5;

function ProgressBar({ step }: { step: number }) {
  return (
    <div style={{ display: "flex", gap: 4, marginBottom: 28 }}>
      {Array.from({ length: STEPS }).map((_, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            height: 3,
            borderRadius: 2,
            background: i < step ? "#00D4AA" : "rgba(255,255,255,0.1)",
            transition: "background 0.3s",
          }}
        />
      ))}
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  fontFamily: "'DM Sans', system-ui, sans-serif",
  fontSize: 13,
  color: "#F0F0F5",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: 10,
};

const radioStyle: React.CSSProperties = {
  width: 16,
  height: 16,
  accentColor: "#00D4AA",
  cursor: "pointer",
  flexShrink: 0,
};

const checkStyle: React.CSSProperties = {
  width: 16,
  height: 16,
  accentColor: "#00D4AA",
  cursor: "pointer",
  flexShrink: 0,
};

export function OnboardingModal({ onComplete, onDismiss }: OnboardingModalProps) {
  const [step, setStep] = useState(1);
  const [done, setDone] = useState(false);

  const [incomeType, setIncomeType] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);
  const [investment, setInvestment] = useState("");
  const [city, setCity] = useState("");
  const [companies, setCompanies] = useState("");

  function toggleSector(s: string) {
    setSectors((prev) =>
      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
    );
  }

  function next() {
    if (step < STEPS) setStep((s) => s + 1);
    else finish();
  }

  function back() {
    setStep((s) => Math.max(1, s - 1));
  }

  function finish() {
    const profile: UserProfile = {
      income_type: incomeType,
      sector_exposure: sectors,
      investment_profile: investment,
      city,
      companies_of_interest: companies,
    };
    setDone(true);
    onComplete(profile);
  }

  const canNext =
    (step === 1 && !!incomeType) ||
    (step === 2 && sectors.length > 0) ||
    (step === 3 && !!investment) ||
    (step === 4 && !!city) ||
    step === 5;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.75)",
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onDismiss();
      }}
    >
      <div
        style={{
          background: "#13131A",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 16,
          padding: "32px 28px",
          width: "min(460px, 100%)",
          position: "relative",
          boxShadow: "0 24px 60px rgba(0,0,0,0.6)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onDismiss}
          style={{
            position: "absolute",
            top: 16,
            right: 16,
            background: "none",
            border: "none",
            color: "#4A4A6A",
            cursor: "pointer",
            fontSize: 20,
            lineHeight: 1,
          }}
          aria-label="Dismiss"
        >
          ×
        </button>

        {!done ? (
          <>
            <h2
              style={{
                fontFamily: "'DM Serif Display', Georgia, serif",
                fontSize: 22,
                color: "#F0F0F5",
                margin: "0 0 6px",
              }}
            >
              Personalize your feed
            </h2>
            <p
              style={{
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontSize: 13,
                color: "#8888AA",
                margin: "0 0 24px",
              }}
            >
              5 quick questions so we can show you what actually matters to you.
            </p>

            <ProgressBar step={step} />

            {step === 1 && (
              <StepSection title="How do you primarily earn?">
                {INCOME_OPTIONS.map((opt) => (
                  <label key={opt} style={labelStyle}>
                    <input
                      type="radio"
                      name="income"
                      value={opt}
                      checked={incomeType === opt}
                      onChange={() => setIncomeType(opt)}
                      style={radioStyle}
                    />
                    {opt}
                  </label>
                ))}
              </StepSection>
            )}

            {step === 2 && (
              <StepSection title="Which sectors are you exposed to?">
                {SECTOR_OPTIONS.map((opt) => (
                  <label key={opt} style={labelStyle}>
                    <input
                      type="checkbox"
                      value={opt}
                      checked={sectors.includes(opt)}
                      onChange={() => toggleSector(opt)}
                      style={checkStyle}
                    />
                    {opt}
                  </label>
                ))}
              </StepSection>
            )}

            {step === 3 && (
              <StepSection title="How is your money currently invested?">
                {INVESTMENT_OPTIONS.map((opt) => (
                  <label key={opt} style={labelStyle}>
                    <input
                      type="radio"
                      name="investment"
                      value={opt}
                      checked={investment === opt}
                      onChange={() => setInvestment(opt)}
                      style={radioStyle}
                    />
                    {opt}
                  </label>
                ))}
              </StepSection>
            )}

            {step === 4 && (
              <StepSection title="Your city">
                <select
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  style={{
                    width: "100%",
                    background: "#0A0A0F",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    padding: "10px 14px",
                    color: city ? "#F0F0F5" : "#8888AA",
                    fontFamily: "'DM Sans', system-ui, sans-serif",
                    fontSize: 14,
                    cursor: "pointer",
                    outline: "none",
                  }}
                >
                  <option value="">Select your city...</option>
                  {CITY_OPTIONS.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </StepSection>
            )}

            {step === 5 && (
              <StepSection title="Companies you watch">
                <textarea
                  value={companies}
                  onChange={(e) => setCompanies(e.target.value)}
                  placeholder="e.g. Infosys, Tata Motors, Apple..."
                  rows={3}
                  style={{
                    width: "100%",
                    background: "#0A0A0F",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    padding: "10px 14px",
                    color: "#F0F0F5",
                    fontFamily: "'DM Sans', system-ui, sans-serif",
                    fontSize: 14,
                    resize: "none",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
                <p
                  style={{
                    fontFamily: "'DM Sans', system-ui, sans-serif",
                    fontSize: 12,
                    color: "#4A4A6A",
                    margin: "4px 0 0",
                  }}
                >
                  Optional — skip if you prefer a general feed.
                </p>
              </StepSection>
            )}

            {/* Buttons */}
            <div style={{ display: "flex", gap: 10, marginTop: 28 }}>
              {step > 1 && (
                <button
                  onClick={back}
                  style={{
                    flex: "0 0 auto",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    padding: "10px 20px",
                    color: "#8888AA",
                    fontFamily: "'DM Sans', system-ui, sans-serif",
                    fontSize: 14,
                    cursor: "pointer",
                  }}
                >
                  Back
                </button>
              )}
              <button
                onClick={next}
                disabled={!canNext}
                style={{
                  flex: 1,
                  background: canNext ? "#00D4AA" : "rgba(255,255,255,0.05)",
                  border: "none",
                  borderRadius: 8,
                  padding: "10px 20px",
                  color: canNext ? "#0A0A0F" : "#4A4A6A",
                  fontFamily: "'DM Sans', system-ui, sans-serif",
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: canNext ? "pointer" : "not-allowed",
                  transition: "all 0.2s",
                }}
              >
                {step === STEPS ? "Start reading →" : "Next →"}
              </button>
            </div>

            <button
              onClick={onDismiss}
              style={{
                width: "100%",
                marginTop: 12,
                background: "none",
                border: "none",
                color: "#4A4A6A",
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontSize: 12,
                cursor: "pointer",
                padding: "4px 0",
              }}
            >
              Skip — show me the general feed
            </button>
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "12px 0" }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}>✓</div>
            <h2
              style={{
                fontFamily: "'DM Serif Display', Georgia, serif",
                fontSize: 22,
                color: "#F0F0F5",
                margin: "0 0 12px",
              }}
            >
              Your feed is personalized.
            </h2>
            <p
              style={{
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontSize: 14,
                color: "#8888AA",
                lineHeight: 1.6,
                margin: "0 0 24px",
              }}
            >
              We'll tell you exactly how each story affects someone like you.
            </p>
            <button
              onClick={onDismiss}
              style={{
                background: "#00D4AA",
                border: "none",
                borderRadius: 8,
                padding: "12px 28px",
                color: "#0A0A0F",
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontSize: 14,
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Start reading →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function StepSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p
        style={{
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 15,
          fontWeight: 600,
          color: "#F0F0F5",
          margin: "0 0 16px",
        }}
      >
        {title}
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>{children}</div>
    </div>
  );
}
