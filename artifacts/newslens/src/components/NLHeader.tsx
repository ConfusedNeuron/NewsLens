import React, { useState } from "react";
import { Link } from "wouter";
import { User, Database, Activity } from "lucide-react";

export type ViewMode = "swipe" | "reel";

interface NLHeaderProps {
  mode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
  onProfileClick: () => void;
}

export function NLHeader({ mode, onModeChange, onProfileClick }: NLHeaderProps) {
  return (
    <header
      style={{
        height: 56,
        background: "#0A0A0F",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        display: "flex",
        alignItems: "center",
        padding: "0 20px",
        position: "sticky",
        top: 0,
        zIndex: 50,
        gap: 16,
      }}
    >
      {/* Wordmark */}
      <div
        style={{
          fontFamily: "'DM Serif Display', Georgia, serif",
          fontSize: 20,
          color: "#F0F0F5",
          letterSpacing: "-0.02em",
          flex: "0 0 auto",
          whiteSpace: "nowrap",
        }}
      >
        NewsLens
      </div>

      {/* Mode toggle — centered */}
      <div
        style={{
          flex: 1,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          role="group"
          aria-label="View mode"
          style={{
            display: "flex",
            background: "rgba(255,255,255,0.05)",
            borderRadius: 8,
            padding: 3,
            gap: 2,
          }}
        >
          <ModeBtn
            active={mode === "swipe"}
            onClick={() => onModeChange("swipe")}
            label="⟵⟶ Swipe"
          />
          <ModeBtn
            active={mode === "reel"}
            onClick={() => onModeChange("reel")}
            label="↕ Scroll"
          />
          <LockedModeBtn />
        </div>
      </div>

      {/* Right side */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, flex: "0 0 auto" }}>
        <Link href="/sources">
          <button
            aria-label="Data sources"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "#8888AA",
              display: "flex",
              alignItems: "center",
              padding: 6,
              borderRadius: 6,
              transition: "color 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#F0F0F5")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#8888AA")}
          >
            <Database size={16} />
          </button>
        </Link>
        <Link href="/pipeline">
          <button
            aria-label="Pipeline logs"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "#8888AA",
              display: "flex",
              alignItems: "center",
              padding: 6,
              borderRadius: 6,
              transition: "color 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#F0F0F5")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#8888AA")}
          >
            <Activity size={16} />
          </button>
        </Link>
        <button
          aria-label="Open profile settings"
          onClick={onProfileClick}
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            background: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.12)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#8888AA",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.14)";
            e.currentTarget.style.color = "#F0F0F5";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.08)";
            e.currentTarget.style.color = "#8888AA";
          }}
        >
          <User size={15} />
        </button>
      </div>
    </header>
  );
}

function ModeBtn({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      style={{
        fontFamily: "'DM Sans', system-ui, sans-serif",
        fontSize: 12,
        fontWeight: 500,
        padding: "5px 12px",
        borderRadius: 6,
        border: "none",
        cursor: "pointer",
        background: active ? "rgba(255,255,255,0.12)" : "transparent",
        color: active ? "#F0F0F5" : "#8888AA",
        transition: "all 0.15s",
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </button>
  );
}

function LockedModeBtn() {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setShowTooltip((v) => !v)}
        aria-expanded={showTooltip}
        aria-haspopup="true"
        style={{
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 12,
          fontWeight: 500,
          padding: "5px 12px",
          borderRadius: 6,
          border: "none",
          cursor: "pointer",
          background: "transparent",
          color: "#4A4A6A",
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        🔒 Deep
      </button>
      {showTooltip && (
        <div
          role="tooltip"
          style={{
            position: "absolute",
            top: "calc(100% + 8px)",
            right: 0,
            width: 260,
            background: "#13131A",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 10,
            padding: "14px 16px",
            zIndex: 100,
            color: "#F0F0F5",
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          <p style={{ marginBottom: 10 }}>
            Nerd Mode gives you the full analysis — sources, raw extractions,
            enrichment data, and cross-domain breakdown.
          </p>
          <a
            href="mailto:hello@newslens.app?subject=Nerd Mode Waitlist"
            style={{ color: "#00D4AA", textDecoration: "none", fontSize: 12 }}
          >
            Join waitlist →
          </a>
          <button
            onClick={() => setShowTooltip(false)}
            aria-label="Close"
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              background: "none",
              border: "none",
              color: "#4A4A6A",
              cursor: "pointer",
              fontSize: 16,
            }}
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
