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
      <div role="tablist" aria-label="Domain filter" style={{ display: "flex", gap: 0, flexShrink: 0 }}>
        {DOMAINS.map((d) => {
          const isActive = domain === d.value;
          const color = d.value ? DOMAIN_COLORS[d.value] : "#F0F0F5";
          return (
            <button
              key={String(d.value)}
              role="tab"
              aria-selected={isActive}
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
                transition: "color 0.15s, border-color 0.15s",
                whiteSpace: "nowrap",
              }}
            >
              {d.icon ? `${d.icon} ${d.label}` : d.label}
            </button>
          );
        })}
      </div>

      <div
        aria-hidden="true"
        style={{
          width: 1,
          height: 20,
          background: "rgba(255,255,255,0.08)",
          flexShrink: 0,
        }}
      />

      {/* Geo pills */}
      <div role="group" aria-label="Geography filter" style={{ display: "flex", gap: 6, flexShrink: 0 }}>
        {GEOS.map((g) => {
          const isSelected = selectedGeos.includes(g.value);
          return (
            <button
              key={g.value}
              aria-pressed={isSelected}
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
        aria-hidden="true"
        style={{
          width: 1,
          height: 20,
          background: "rgba(255,255,255,0.08)",
          flexShrink: 0,
          marginLeft: "auto",
        }}
      />

      {/* Confidence toggle — proper checkbox for accessibility */}
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
        <input
          type="checkbox"
          checked={showUncertain}
          onChange={onShowUncertainToggle}
          style={{
            appearance: "none",
            WebkitAppearance: "none",
            width: 28,
            height: 16,
            borderRadius: 8,
            background: showUncertain ? "#6B7280" : "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.1)",
            position: "relative",
            cursor: "pointer",
            flexShrink: 0,
            transition: "background 0.2s",
            outline: "none",
          }}
          aria-label="Show uncertain cards"
        />
        <span
          style={{
            pointerEvents: "none",
            position: "relative",
            display: "inline-block",
          }}
        />
        Show uncertain
      </label>
    </div>
  );
}
