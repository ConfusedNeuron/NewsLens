export const DOMAINS = [
  { label: "All", value: null, icon: null },
  { label: "Finance", value: "Finance", icon: "📈" },
  { label: "Tech", value: "Tech", icon: "⚡" },
  { label: "Geopolitics", value: "Geopolitics", icon: "🌐" },
  { label: "Environment", value: "Environment", icon: "🌱" },
];

export const DOMAIN_COLORS: Record<string, string> = {
  Finance: "#00D4AA",
  Tech: "#7C6FFF",
  Geopolitics: "#FF6B35",
  Environment: "#4ADE80",
};

export const GEOS = [
  { label: "🌍 Global", value: "Global" },
  { label: "🇮🇳 India", value: "India" },
  { label: "🇺🇸 USA", value: "USA" },
  { label: "🇨🇳 China", value: "China" },
];

interface NLFilterBarProps {
  domain: string | null;
  onDomainChange: (d: string | null) => void;
  selectedGeos: string[];
  onGeoToggle: (geo: string) => void;
  showUncertain: boolean;
  onShowUncertainToggle: () => void;
}

export function NLFilterBar({
  domain,
  onDomainChange,
  selectedGeos,
  onGeoToggle,
  showUncertain,
  onShowUncertainToggle,
}: NLFilterBarProps) {
  const activeColor = domain ? DOMAIN_COLORS[domain] ?? "#F0F0F5" : "#F0F0F5";

  return (
    <div
      style={{
        background: "#0A0A0F",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        padding: "0 20px",
        display: "flex",
        alignItems: "center",
        gap: 20,
        overflowX: "auto",
        minHeight: 44,
        flexShrink: 0,
      }}
    >
      {/* Domain tabs */}
      <div style={{ display: "flex", gap: 0, flexShrink: 0 }}>
        {DOMAINS.map((d) => {
          const isActive = domain === d.value;
          const color = d.value ? DOMAIN_COLORS[d.value] : "#F0F0F5";
          return (
            <button
              key={String(d.value)}
              onClick={() => onDomainChange(d.value)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "10px 14px",
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? color : "#8888AA",
                borderBottom: isActive ? `2px solid ${color}` : "2px solid transparent",
                transition: "all 0.15s",
                whiteSpace: "nowrap",
              }}
            >
              {d.icon ? `${d.icon} ${d.label}` : d.label}
            </button>
          );
        })}
      </div>

      <div
        style={{
          width: 1,
          height: 20,
          background: "rgba(255,255,255,0.08)",
          flexShrink: 0,
        }}
      />

      {/* Geo pills */}
      <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {GEOS.map((g) => {
          const isSelected = selectedGeos.includes(g.value);
          return (
            <button
              key={g.value}
              onClick={() => onGeoToggle(g.value)}
              style={{
                background: isSelected ? "rgba(255,255,255,0.12)" : "transparent",
                border: "1px solid",
                borderColor: isSelected ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.08)",
                borderRadius: 20,
                padding: "3px 10px",
                cursor: "pointer",
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontSize: 12,
                color: isSelected ? "#F0F0F5" : "#8888AA",
                transition: "all 0.15s",
                whiteSpace: "nowrap",
              }}
            >
              {g.label}
            </button>
          );
        })}
      </div>

      <div
        style={{
          width: 1,
          height: 20,
          background: "rgba(255,255,255,0.08)",
          flexShrink: 0,
          marginLeft: "auto",
        }}
      />

      {/* Confidence toggle */}
      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          cursor: "pointer",
          flexShrink: 0,
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 12,
          color: showUncertain ? "#F0F0F5" : "#8888AA",
          whiteSpace: "nowrap",
        }}
      >
        <div
          onClick={onShowUncertainToggle}
          style={{
            width: 28,
            height: 16,
            borderRadius: 8,
            background: showUncertain ? "#6B7280" : "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.1)",
            position: "relative",
            cursor: "pointer",
            transition: "background 0.2s",
            flexShrink: 0,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 2,
              left: showUncertain ? 13 : 2,
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: showUncertain ? "#F0F0F5" : "#4A4A6A",
              transition: "left 0.2s",
            }}
          />
        </div>
        Show uncertain
      </label>
    </div>
  );
}
