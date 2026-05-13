import { useEffect, useState } from "react";
import { motion, useMotionValue, useTransform, useAnimation, useReducedMotion, type PanInfo } from "framer-motion";
import type { Card } from "@/api";
import { NewsCard, UserProfile } from "./NewsCard";
import { useSaveSwipe } from "./swipe-utils";

interface SwipeModeProps {
  cards: Card[];
  profile: UserProfile | null;
  onSwipe: (cardId: string, direction: "left" | "right") => void;
  onDone: () => void;
}

const CARD_W = "min(480px, 90vw)";
const CARD_H = "min(680px, 85vh)";

export function SwipeMode({ cards, profile, onSwipe, onDone }: SwipeModeProps) {
  const [idx, setIdx] = useState(0);
  const saveSwipe = useSaveSwipe();

  function handleDismiss(direction: "left" | "right") {
    const card = cards[idx];
    if (card) {
      saveSwipe(card.id, direction);
      onSwipe(card.id, direction);
    }
    const next = idx + 1;
    if (next >= cards.length) {
      onDone();
    } else {
      setIdx(next);
    }
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft") handleDismiss("left");
      if (e.key === "ArrowRight") handleDismiss("right");
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [idx, cards]);

  if (idx >= cards.length) return null;

  const visible = cards.slice(idx, idx + 3);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        flex: 1,
        padding: "16px 0 80px",
        minHeight: 0,
      }}
    >
      {/* Card stack */}
      <div
        style={{
          position: "relative",
          width: CARD_W,
          height: CARD_H,
        }}
      >
        {[...visible].reverse().map((card, reverseIdx) => {
          const depth = visible.length - 1 - reverseIdx;
          return (
            <SwipeCard
              key={card.id}
              card={card}
              depth={depth}
              profile={profile}
              onDismiss={handleDismiss}
              isActive={depth === 0}
            />
          );
        })}
      </div>

      {/* Skip / Save buttons */}
      <div
        style={{
          display: "flex",
          gap: 32,
          marginTop: 24,
          alignItems: "center",
        }}
      >
        <button
          onClick={() => handleDismiss("left")}
          aria-label="Skip this card"
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            border: "1px solid rgba(239,68,68,0.3)",
            background: "rgba(239,68,68,0.08)",
            color: "#EF4444",
            fontSize: 22,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(239,68,68,0.18)";
            e.currentTarget.style.borderColor = "rgba(239,68,68,0.6)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(239,68,68,0.08)";
            e.currentTarget.style.borderColor = "rgba(239,68,68,0.3)";
          }}
        >
          ✕
        </button>
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            color: "#4A4A6A",
          }}
        >
          {idx + 1}/{cards.length}
        </span>
        <button
          onClick={() => handleDismiss("right")}
          aria-label="Save this card"
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            border: "1px solid rgba(34,197,94,0.3)",
            background: "rgba(34,197,94,0.08)",
            color: "#22C55E",
            fontSize: 22,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(34,197,94,0.18)";
            e.currentTarget.style.borderColor = "rgba(34,197,94,0.6)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(34,197,94,0.08)";
            e.currentTarget.style.borderColor = "rgba(34,197,94,0.3)";
          }}
        >
          ★
        </button>
      </div>
    </div>
  );
}

function SwipeCard({
  card,
  depth,
  profile,
  onDismiss,
  isActive,
}: {
  card: Card;
  depth: number;
  profile: UserProfile | null;
  onDismiss: (dir: "left" | "right") => void;
  isActive: boolean;
}) {
  const reducedMotion = useReducedMotion();
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-300, 300], reducedMotion ? [0, 0] : [-18, 18]);
  const skipOpacity = useTransform(x, [-160, -40, 0], [1, 0.4, 0]);
  const saveOpacity = useTransform(x, [0, 40, 160], [0, 0.4, 1]);
  const controls = useAnimation();

  const scale = depth === 0 ? 1 : depth === 1 ? 0.96 : 0.92;
  const yOffset = depth === 0 ? 0 : depth === 1 ? 10 : 20;

  // When reduced motion is preferred, transitions are instant (duration: 0)
  const springTransition = reducedMotion
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 300, damping: 28 };
  const dismissTransition = reducedMotion
    ? { duration: 0 }
    : { duration: 0.28, ease: "easeIn" as const };
  const snapTransition = reducedMotion
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 380, damping: 30 };

  async function handleDragEnd(_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) {
    const threshold = Math.min(480, window.innerWidth * 0.9) * 0.38;
    const shouldDismiss =
      Math.abs(info.offset.x) > threshold || Math.abs(info.velocity.x) > 550;

    if (shouldDismiss) {
      const direction = info.offset.x > 0 ? "right" : "left";
      await controls.start({
        x: direction === "right" ? 1200 : -1200,
        rotate: reducedMotion ? 0 : direction === "right" ? 20 : -20,
        opacity: 0,
        transition: dismissTransition,
      });
      onDismiss(direction);
    } else {
      controls.start({ x: 0, rotate: 0, transition: snapTransition });
    }
  }

  return (
    <motion.div
      animate={{ scale, y: yOffset, ...(!isActive ? {} : {}) }}
      transition={springTransition}
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 3 - depth,
      }}
    >
      <motion.div
        drag={isActive ? "x" : false}
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.9}
        onDragEnd={isActive ? handleDragEnd : undefined}
        animate={controls}
        style={{ x: isActive ? x : 0, rotate: isActive ? rotate : 0, width: "100%", height: "100%", position: "relative" }}
        whileDrag={{ cursor: "grabbing" }}
        initial={false}
      >
        {/* Skip hint overlay */}
        {isActive && (
          <motion.div
            style={{
              opacity: skipOpacity,
              position: "absolute",
              inset: 0,
              background: "rgba(239,68,68,0.18)",
              borderRadius: 16,
              zIndex: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-start",
              paddingLeft: 28,
              pointerEvents: "none",
            }}
          >
            <span
              style={{
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontWeight: 700,
                fontSize: 28,
                color: "#EF4444",
                letterSpacing: "-0.01em",
              }}
            >
              ✕ SKIP
            </span>
          </motion.div>
        )}

        {/* Save hint overlay */}
        {isActive && (
          <motion.div
            style={{
              opacity: saveOpacity,
              position: "absolute",
              inset: 0,
              background: "rgba(34,197,94,0.18)",
              borderRadius: 16,
              zIndex: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              paddingRight: 28,
              pointerEvents: "none",
            }}
          >
            <span
              style={{
                fontFamily: "'DM Sans', system-ui, sans-serif",
                fontWeight: 700,
                fontSize: 28,
                color: "#22C55E",
                letterSpacing: "-0.01em",
              }}
            >
              ★ SAVE
            </span>
          </motion.div>
        )}

        <NewsCard card={card} profile={profile} />
      </motion.div>
    </motion.div>
  );
}
