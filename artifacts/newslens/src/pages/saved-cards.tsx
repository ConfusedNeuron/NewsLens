import { Link } from "wouter";

export default function SavedCards() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0A0A0F",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        fontFamily: "'DM Sans', system-ui, sans-serif",
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: "50%",
          background: "rgba(0,212,170,0.1)",
          border: "1px solid rgba(0,212,170,0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 24,
        }}
      >
        ★
      </div>
      <p
        style={{
          fontFamily: "'DM Serif Display', Georgia, serif",
          fontSize: 22,
          color: "#F0F0F5",
          margin: 0,
        }}
      >
        Saved cards
      </p>
      <p
        style={{
          fontSize: 14,
          color: "#8888AA",
          margin: 0,
          textAlign: "center",
          maxWidth: 320,
        }}
      >
        Cards you save while swiping will appear here. This view is coming soon.
      </p>
      <Link href="/">
        <button
          style={{
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
            padding: "8px 20px",
            color: "#F0F0F5",
            fontSize: 13,
            cursor: "pointer",
            marginTop: 8,
            fontFamily: "'DM Sans', system-ui, sans-serif",
          }}
        >
          ← Back to feed
        </button>
      </Link>
    </div>
  );
}
