import type { Card, Winner } from "@workspace/api-client-react";
import { DOMAIN_COLORS } from "./NLFilterBar";

/**
 * Renders one winner or loser, distinguishing sourced figures from model estimates.
 *
 * Magnitudes marked `estimate` are the model's own inference rather than something
 * read out of the enrichment payload. They are shown — suppressing them would empty
 * most cards while RSS snippets are the only input — but they are visually demoted
 * and labelled, so a reader can tell at a glance which numbers to lean on.
 * Anything without an explicit "data" label is treated as an estimate.
 */
function ImpactRow({ item, kind }: { item: Winner; kind: "winner" | "loser" }) {
  const isWinner = kind === "winner";
  const isSourced = item.magnitude_source === "data";

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
      <span style={{ fontSize: 14, flexShrink: 0, marginTop: 1 }}>{isWinner ? "✅" : "❌"}</span>
      <div style={{ minWidth: 0 }}>
        <span
          style={{
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: 12,
            fontWeight: 600,
            color: isWinner ? "#22C55E" : "#EF4444",
          }}
        >
          {item.who}
        </span>
        <span
          style={{
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: 12,
            color: "#8888AA",
          }}
        >
          {" · "}
          {item.why}
        </span>
        {item.magnitude && (
          <span
            style={{
              fontFamily: "'DM Sans', system-ui, sans-serif",
              fontSize: 12,
              color: isSourced ? "#8888AA" : "#5F5F7A",
              fontStyle: isSourced ? "normal" : "italic",
            }}
            title={
              isSourced
                ? "Figure taken from market data or from the source article."
                : "Model estimate — not from a verified data source."
            }
          >
            {" · "}
            {!isSourced && (
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                  color: "#6B6B8A",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: 4,
                  padding: "1px 4px",
                  marginRight: 4,
                  fontStyle: "normal",
                }}
                aria-label="Model estimate, not from a verified data source"
              >
                est
              </span>
            )}
            {item.magnitude}
          </span>
        )}
      </div>
    </div>
  );
}

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

const HORIZON_LABELS: Record<string, string> = {
  immediate: "⏱ Immediate",
  short: "⏱ Near-term",
  long: "⏱ Long-term",
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

      {/* Row 4: Key number + time horizon chips */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", flexShrink: 0 }}>
        {card.key_number && (
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
        )}
        {/* Real horizon from the card. This read "Near-term" on every card for months
            because time_horizon existed in the pipeline but never reached the API. */}
        {card.time_horizon && (
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: compact ? 12 : 13,
              fontWeight: 600,
              color: "#8888AA",
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 6,
              padding: "4px 10px",
            }}
            title="Time horizon over which this story's impact plays out"
          >
            {HORIZON_LABELS[card.time_horizon] ?? "⏱ Near-term"}
          </span>
        )}
      </div>

      {/* Market data the analysis was anchored to. Enrichment was fetched from
          yfinance/FRED and fed to the model but never shown, so a reader had no way
          to check the numbers behind a claim. Hidden entirely when empty. */}
      {(card.market_data?.length ?? 0) > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", flexShrink: 0 }}>
          {card.market_data!.slice(0, compact ? 3 : 5).map((q) => {
            const up = (q.pct_change_1d ?? 0) > 0;
            const flat = !q.pct_change_1d;
            return (
              <span
                key={`${q.label}-${q.symbol ?? ""}`}
                title={q.symbol ? `${q.label} (${q.symbol})` : q.label}
                style={{
                  display: "inline-flex",
                  alignItems: "baseline",
                  gap: 4,
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  borderRadius: 5,
                  padding: "2px 6px",
                  color: "#8888AA",
                }}
              >
                <span>{q.label}</span>
                {q.price != null && (
                  <span style={{ color: "#C8C8DC" }}>
                    {q.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </span>
                )}
                {!flat && (
                  <span style={{ color: up ? "#22C55E" : "#EF4444" }}>
                    {up ? "▲" : "▼"}
                    {Math.abs(q.pct_change_1d!).toFixed(2)}%
                  </span>
                )}
              </span>
            );
          })}
        </div>
      )}

      {/* Divider */}
      <div style={{ height: 1, background: "rgba(255,255,255,0.06)", flexShrink: 0 }} />

      {/* Row 5+6: Winners & Losers */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>
        {/* Show up to 2 of each. The detail page already mapped full arrays; the feed
            card previously showed only [0], so a card with a second, often more
            relevant, winner silently hid it. `compact` keeps reel mode to one each. */}
        {(card.winners ?? []).slice(0, compact ? 1 : 2).map((w, i) => (
          <ImpactRow key={`w${i}`} item={w} kind="winner" />
        ))}
        {(card.losers ?? []).slice(0, compact ? 1 : 2).map((l, i) => (
          <ImpactRow key={`l${i}`} item={l} kind="loser" />
        ))}
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

      {/* Row 9: Disclaimer. Not decoration — this card names winners and losers and
          attaches figures to them, some of which are model estimates. Flagged as a
          legal risk in the consultant report; kept on every card, including compact. */}
      <p
        style={{
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 9,
          lineHeight: 1.4,
          color: "#3F3F5A",
          margin: 0,
          flexShrink: 0,
        }}
      >
        Automated analysis, not financial advice. Figures marked “est” are model
        estimates, not verified data.
      </p>
    </div>
  );
}
