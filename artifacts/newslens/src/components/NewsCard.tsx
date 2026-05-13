import type { Card } from "@workspace/api-client-react";
import { DOMAIN_COLORS } from "./NLFilterBar";

export interface UserProfile {
  income_type: string;
  sector_exposure: string[];
  investment_profile: string;
  city: string;
  companies_of_interest: string;
}

interface NewsCardProps {
  card: Card;
  profile?: UserProfile | null;
  compact?: boolean;
}

const DOMAIN_ICONS: Record<string, string> = {
  Finance: "📈",
  Tech: "⚡",
  Geopolitics: "🌐",
  Environment: "🌱",
};

const CONFIDENCE_CONFIG = {
  high: { dot: "#22C55E", label: "High Confidence", color: "#22C55E" },
  medium: { dot: "#F59E0B", label: "Est.", color: "#F59E0B" },
  low: { dot: "#6B7280", label: "Uncertain", color: "#6B7280" },
};

export function NewsCard({ card, profile, compact }: NewsCardProps) {
  const domains = card.tags?.domain ?? [];
  const geos = card.tags?.geo ?? [];
  const primaryDomain = domains[0] ?? "";
  const domainColor = DOMAIN_COLORS[primaryDomain] ?? "#8888AA";
  const conf = CONFIDENCE_CONFIG[card.confidence as keyof typeof CONFIDENCE_CONFIG] ?? CONFIDENCE_CONFIG.medium;
  const hasProfile = !!profile;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#13131A",
        borderRadius: 16,
        border: "1px solid rgba(255,255,255,0.08)",
        display: "flex",
        flexDirection: "column",
        padding: compact ? "16px" : "20px 24px",
        overflow: "hidden",
        boxSizing: "border-box",
        gap: compact ? 10 : 14,
        userSelect: "none",
      }}
    >
      {/* Row 1: Domain pill + Confidence badge */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexShrink: 0 }}>
        <div
          style={{
            display: "flex",
            gap: 6,
            flexWrap: "wrap",
          }}
        >
          {domains.map((d) => (
            <span
              key={d}
              style={{
                background: `${DOMAIN_COLORS[d] ?? "#8888AA"}18`,
                color: DOMAIN_COLORS[d] ?? "#8888AA",
                border: `1px solid ${DOMAIN_COLORS[d] ?? "#8888AA"}40`,
                borderRadius: 20,
                padding: "2px 10px",
                fontSize: 11,
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontWeight: 600,
                letterSpacing: "0.04em",
              }}
            >
              {DOMAIN_ICONS[d] && `${DOMAIN_ICONS[d]} `}{d.toUpperCase()}
            </span>
          ))}
        </div>
        <span
          aria-label={`Confidence level: ${conf.label}`}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            background: `${conf.dot}14`,
            border: `1px solid ${conf.dot}40`,
            borderRadius: 20,
            padding: "2px 10px",
            fontSize: 11,
            fontFamily: "'JetBrains Mono', monospace",
            color: conf.color,
            flexShrink: 0,
            marginLeft: 8,
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: conf.dot,
              flexShrink: 0,
            }}
          />
          {conf.label}
        </span>
      </div>

      {/* Row 2: Headline */}
      <h2
        style={{
          fontFamily: "'DM Serif Display', Georgia, serif",
          fontSize: compact ? 20 : 24,
          lineHeight: 1.25,
          color: "#F0F0F5",
          margin: 0,
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          flexShrink: 0,
        }}
      >
        {card.headline}
      </h2>

      {/* Row 3: Summary */}
      <p
        style={{
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: compact ? 13 : 14,
          lineHeight: 1.55,
          color: "#8888AA",
          margin: 0,
          display: "-webkit-box",
          WebkitLineClamp: compact ? 3 : 4,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          flexShrink: 0,
        }}
      >
        {card.summary}
      </p>

      {/* Row 4: Key number chip */}
      {card.key_number && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", flexShrink: 0 }}>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: compact ? 12 : 13,
              fontWeight: 600,
              color: domainColor,
              background: `${domainColor}10`,
              border: `1px solid ${domainColor}30`,
              borderRadius: 6,
              padding: "4px 10px",
            }}
          >
            {card.key_number}
          </span>
        </div>
      )}

      {/* Divider */}
      <div style={{ height: 1, background: "rgba(255,255,255,0.06)", flexShrink: 0 }} />

      {/* Row 5+6: Winners & Losers */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>
        {card.winners && card.winners.length > 0 && (
          <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
            <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>✅</span>
            <div style={{ minWidth: 0 }}>
              <span
                style={{
                  fontFamily: "'DM Sans', system-ui, sans-serif",
                  fontSize: 12,
                  fontWeight: 600,
                  color: "#22C55E",
                }}
              >
                {card.winners[0].who}
              </span>
              <span
                style={{
                  fontFamily: "'DM Sans', system-ui, sans-serif",
                  fontSize: 12,
                  color: "#8888AA",
                }}
              >
                {" · "}
                {card.winners[0].why}
                {card.winners[0].magnitude && ` · ${card.winners[0].magnitude}`}
              </span>
            </div>
          </div>
        )}
        {card.losers && card.losers.length > 0 && (
          <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
            <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>❌</span>
            <div style={{ minWidth: 0 }}>
              <span
                style={{
                  fontFamily: "'DM Sans', system-ui, sans-serif",
                  fontSize: 12,
                  fontWeight: 600,
                  color: "#EF4444",
                }}
              >
                {card.losers[0].who}
              </span>
              <span
                style={{
                  fontFamily: "'DM Sans', system-ui, sans-serif",
                  fontSize: 12,
                  color: "#8888AA",
                }}
              >
                {" · "}
                {card.losers[0].why}
                {card.losers[0].magnitude && ` · ${card.losers[0].magnitude}`}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Row 7: Personal impact (only if profile exists and impact text is present) */}
      {hasProfile && card.personal_impact && (
        <>
          <div style={{ height: 1, background: "rgba(255,255,255,0.06)", flexShrink: 0 }} />
          <div
            style={{
              display: "flex",
              gap: 8,
              alignItems: "flex-start",
              background: "rgba(0,212,170,0.06)",
              border: "1px solid rgba(0,212,170,0.15)",
              borderRadius: 8,
              padding: "8px 12px",
              flexShrink: 0,
            }}
          >
            <span style={{ fontSize: 13, flexShrink: 0 }}>👤</span>
            <p
              style={{
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontSize: 12,
                color: "#00D4AA",
                margin: 0,
                lineHeight: 1.5,
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {card.personal_impact}
            </p>
          </div>
        </>
      )}

      {/* Row 8: Geo tags + source */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "auto",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {geos.map((g) => (
            <span
              key={g}
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 20,
                padding: "2px 8px",
                fontSize: 11,
                fontFamily: "'DM Sans', system-ui, sans-serif",
                color: "#8888AA",
              }}
            >
              {g === "India" ? "🇮🇳 India" : g === "USA" ? "🇺🇸 USA" : g === "China" ? "🇨🇳 China" : `🌍 ${g}`}
            </span>
          ))}
        </div>
        {card.source && (
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: "#4A4A6A",
              letterSpacing: "0.04em",
            }}
          >
            {card.source.name}
          </span>
        )}
      </div>
    </div>
  );
}
