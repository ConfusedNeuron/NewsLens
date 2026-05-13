import { useRef, useEffect, useState } from "react";
import { Card } from "@workspace/api-client-react/src/generated/api.schemas";
import { NewsCard, UserProfile } from "./NewsCard";

interface ReelModeProps {
  cards: Card[];
  profile: UserProfile | null;
}

export function ReelMode({ cards, profile }: ReelModeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentIdx, setCurrentIdx] = useState(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    function onScroll() {
      const scrollTop = el!.scrollTop;
      const idx = Math.round(scrollTop / el!.clientHeight);
      setCurrentIdx(Math.min(idx, cards.length - 1));
    }

    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [cards.length]);

  return (
    <div style={{ position: "relative", flex: 1, minHeight: 0 }}>
      {/* Scroll container */}
      <div
        ref={containerRef}
        style={{
          overflowY: "scroll",
          scrollSnapType: "y mandatory",
          height: "100%",
          scrollbarWidth: "none",
        }}
      >
        {cards.map((card, i) => (
          <div
            key={card.id}
            style={{
              height: "100%",
              scrollSnapAlign: "start",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "20px 16px",
              boxSizing: "border-box",
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: "min(640px, 100%)",
                height: "min(680px, 100%)",
                maxHeight: "calc(100% - 16px)",
              }}
            >
              <NewsCard card={card} profile={profile} />
            </div>
          </div>
        ))}
      </div>

      {/* Progress bar — right edge */}
      <div
        style={{
          position: "absolute",
          top: 16,
          right: 12,
          bottom: 16,
          width: 3,
          background: "rgba(255,255,255,0.06)",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: cards.length > 1 ? `${((currentIdx) / (cards.length - 1)) * 100}%` : "100%",
            background: "#00D4AA",
            borderRadius: 2,
            transition: "height 0.3s ease",
          }}
        />
      </div>

      {/* Dot indicators — bottom center */}
      <div
        style={{
          position: "absolute",
          bottom: 16,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 6,
          alignItems: "center",
        }}
      >
        {cards.map((_, i) => (
          <div
            key={i}
            style={{
              width: i === currentIdx ? 16 : 6,
              height: 6,
              borderRadius: 3,
              background: i === currentIdx ? "#00D4AA" : "rgba(255,255,255,0.15)",
              transition: "all 0.2s ease",
              cursor: "pointer",
            }}
            onClick={() => {
              const el = containerRef.current;
              if (el) {
                el.scrollTo({ top: i * el.clientHeight, behavior: "smooth" });
              }
            }}
          />
        ))}
      </div>
    </div>
  );
}
