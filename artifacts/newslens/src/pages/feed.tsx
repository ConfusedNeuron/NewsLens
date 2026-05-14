import { useState, useEffect } from "react";
import { useListCards, getListCardsQueryKey, useUpdateUserProfile } from "@/api";
import type { Card } from "@/api";
import { NLHeader, ViewMode } from "@/components/NLHeader";
import { NLFilterBar } from "@/components/NLFilterBar";
import { SwipeMode } from "@/components/SwipeMode";
import { ReelMode } from "@/components/ReelMode";
import { OnboardingModal } from "@/components/OnboardingModal";
import { UserProfile } from "@/components/NewsCard";

const LS_PROFILE = "newslens_profile";
const LS_MODE = "newslens_mode";
const LS_DOMAIN = "newslens_domain";
const LS_GEOS = "newslens_geos";
const LS_UNCERTAIN = "newslens_uncertain";
const LS_ONBOARDED = "newslens_onboarded";

function loadLS<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function saveLS(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {}
}

export default function Feed() {
  const [mode, setMode] = useState<ViewMode>(() => loadLS(LS_MODE, "swipe"));
  const [domain, setDomain] = useState<string | null>(() => loadLS(LS_DOMAIN, null));
  const [geos, setGeos] = useState<string[]>(() => loadLS(LS_GEOS, []));
  const [showUncertain, setShowUncertain] = useState<boolean>(() => loadLS(LS_UNCERTAIN, false));
  const [profile, setProfile] = useState<UserProfile | null>(() => loadLS(LS_PROFILE, null));
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [swipeQueue, setSwipeQueue] = useState<Card[] | null>(null);
  const [feedDone, setFeedDone] = useState(false);

  const saveProfileMutation = useUpdateUserProfile();

  const params = {
    limit: 50,
    page: 1,
    ...(domain ? { domain } : {}),
  };

  const { data, isLoading, error } = useListCards(params, {
    query: { queryKey: getListCardsQueryKey(params) },
  });

  // Show onboarding on first visit (no profile AND not explicitly dismissed)
  useEffect(() => {
    const onboarded = loadLS(LS_ONBOARDED, false);
    if (!onboarded && !profile) {
      setShowOnboarding(true);
    }
  }, []);

  // Persist filter/mode state
  useEffect(() => { saveLS(LS_MODE, mode); }, [mode]);
  useEffect(() => { saveLS(LS_DOMAIN, domain); }, [domain]);
  useEffect(() => { saveLS(LS_GEOS, geos); }, [geos]);
  useEffect(() => { saveLS(LS_UNCERTAIN, showUncertain); }, [showUncertain]);

  function handleModeChange(m: ViewMode) {
    setMode(m);
    setFeedDone(false);
  }

  function handleDomainChange(d: string | null) {
    setDomain(d);
    setSwipeQueue(null);
    setFeedDone(false);
  }

  function handleGeoToggle(geo: string) {
    setGeos((prev) =>
      prev.includes(geo) ? prev.filter((g) => g !== geo) : [...prev, geo]
    );
    setSwipeQueue(null);
    setFeedDone(false);
  }

  function handleShowUncertainToggle() {
    setShowUncertain((v) => !v);
    setSwipeQueue(null);
    setFeedDone(false);
  }

  function resetFilters() {
    setDomain(null);
    setGeos([]);
    setShowUncertain(false);
    setSwipeQueue(null);
    setFeedDone(false);
  }

  function handleOnboardingComplete(p: UserProfile) {
    setProfile(p);
    saveLS(LS_PROFILE, p);
    saveLS(LS_ONBOARDED, true);
    // POST to API
    saveProfileMutation.mutate({
      data: {
        user_id: "default_user",
        income_type: p.income_type,
        sector_exposure: p.sector_exposure.join(", "),
        investment_profile: p.investment_profile,
        city: p.city,
        companies_of_interest: p.companies_of_interest,
      },
    });
  }

  function handleOnboardingDismiss() {
    setShowOnboarding(false);
    saveLS(LS_ONBOARDED, true);
  }

  function handleProfileClick() {
    setShowOnboarding(true);
  }

  function handleSwipe(cardId: string, direction: "left" | "right") {
    // Swipe recorded via SwipeMode internally
  }

  // Apply client-side filters: geo + confidence
  const allCards: Card[] = data?.cards ?? [];
  const filteredCards = allCards.filter((c) => {
    if (!showUncertain && c.confidence === "low") return false;
    if (geos.length > 0) {
      const cardGeos = c.tags?.geo ?? [];
      const hasMatch = geos.some((g) => cardGeos.includes(g));
      if (!hasMatch) return false;
    }
    return true;
  });

  // Initialise swipe queue when cards load or filters change
  useEffect(() => {
    if (!isLoading && filteredCards.length > 0 && swipeQueue === null) {
      setSwipeQueue(filteredCards);
      setFeedDone(false);
    }
  }, [isLoading, filteredCards.length, swipeQueue]);

  const displayCards = mode === "swipe" ? (swipeQueue ?? filteredCards) : filteredCards;
  const isEmpty = !isLoading && filteredCards.length === 0;

  return (
    <div
      style={{
        height: "100dvh",
        display: "flex",
        flexDirection: "column",
        background: "#0A0A0F",
        color: "#F0F0F5",
        overflow: "hidden",
      }}
    >
      {/* Onboarding modal */}
      {showOnboarding && (
        <OnboardingModal
          onComplete={(p) => {
            handleOnboardingComplete(p);
          }}
          onDismiss={handleOnboardingDismiss}
        />
      )}

      {/* Header */}
      <NLHeader
        mode={mode}
        onModeChange={handleModeChange}
        onProfileClick={handleProfileClick}
      />

      {/* Filter bar */}
      <NLFilterBar
        domain={domain}
        onDomainChange={handleDomainChange}
        selectedGeos={geos}
        onGeoToggle={handleGeoToggle}
        showUncertain={showUncertain}
        onShowUncertainToggle={handleShowUncertainToggle}
      />

      {/* Main content area */}
      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {isLoading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState />
        ) : isEmpty ? (
          <EmptyState onReset={resetFilters} />
        ) : feedDone && mode === "swipe" ? (
          <DoneState onReset={() => { setSwipeQueue(null); setFeedDone(false); }} />
        ) : mode === "swipe" ? (
          <SwipeMode
            cards={displayCards}
            profile={profile}
            onSwipe={handleSwipe}
            onDone={() => setFeedDone(true)}
          />
        ) : (
          <ReelMode cards={displayCards} profile={profile} />
        )}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 20,
      }}
    >
      {/* Skeleton card */}
      <div
        style={{
          width: "min(480px, 90vw)",
          height: "min(680px, 85vh)",
          background: "#13131A",
          borderRadius: 16,
          border: "1px solid rgba(255,255,255,0.06)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 50%, transparent 100%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s linear infinite",
          }}
        />
        <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <div style={{ width: 80, height: 24, background: "rgba(255,255,255,0.06)", borderRadius: 20 }} />
            <div style={{ width: 100, height: 24, background: "rgba(255,255,255,0.06)", borderRadius: 20 }} />
          </div>
          <div style={{ width: "90%", height: 32, background: "rgba(255,255,255,0.06)", borderRadius: 4 }} />
          <div style={{ width: "70%", height: 32, background: "rgba(255,255,255,0.06)", borderRadius: 4 }} />
          <div style={{ height: 20 }} />
          {[1, 2, 3, 4].map((i) => (
            <div key={i} style={{ width: `${95 - i * 5}%`, height: 14, background: "rgba(255,255,255,0.04)", borderRadius: 4 }} />
          ))}
          <div style={{ height: 20 }} />
          <div style={{ width: 120, height: 32, background: "rgba(255,255,255,0.06)", borderRadius: 6 }} />
        </div>
      </div>
      <p
        style={{
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 13,
          color: "#4A4A6A",
        }}
      >
        Fetching latest intelligence...
      </p>
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
}

function ErrorState() {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#EF4444",
        fontFamily: "'DM Sans', system-ui, sans-serif",
        fontSize: 14,
      }}
    >
      Failed to load feed — check your connection.
    </div>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        color: "#8888AA",
      }}
    >
      <span style={{ fontSize: 40 }}>📭</span>
      <p
        style={{
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 15,
          color: "#8888AA",
          margin: 0,
        }}
      >
        No cards match your current filters.
      </p>
      <button
        onClick={onReset}
        style={{
          background: "rgba(255,255,255,0.06)",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 8,
          padding: "8px 20px",
          color: "#F0F0F5",
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 13,
          cursor: "pointer",
          transition: "all 0.15s",
        }}
      >
        Reset filters
      </button>
    </div>
  );
}

function useNextUpdateCountdown() {
  const [label, setLabel] = useState("");

  useEffect(() => {
    function compute() {
      const now = new Date();
      // Next update at the next 6-hour boundary: 0:00, 6:00, 12:00, 18:00
      const nextH = Math.ceil((now.getHours() + now.getMinutes() / 60) / 6) * 6;
      const next = new Date(now);
      next.setHours(nextH % 24, 0, 0, 0);
      if (next <= now) next.setDate(next.getDate() + 1);
      const diffMs = next.getTime() - now.getTime();
      const h = Math.floor(diffMs / 3600000);
      const m = Math.floor((diffMs % 3600000) / 60000);
      if (h > 0) setLabel(`${h}h ${m}m`);
      else setLabel(`${m}m`);
    }
    compute();
    const id = setInterval(compute, 60000);
    return () => clearInterval(id);
  }, []);

  return label;
}

function DoneState({ onReset }: { onReset: () => void }) {
  const countdown = useNextUpdateCountdown();
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
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
          color: "#00D4AA",
        }}
      >
        ✓
      </div>
      <p
        style={{
          fontFamily: "'DM Serif Display', Georgia, serif",
          fontSize: 22,
          color: "#F0F0F5",
          margin: 0,
        }}
      >
        You're caught up.
      </p>
      <p
        style={{
          fontFamily: "'DM Sans', system-ui, sans-serif",
          fontSize: 14,
          color: "#8888AA",
          margin: 0,
        }}
      >
        {countdown ? `Next update in ${countdown}.` : "Next update in a few hours."}
      </p>
      <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
        <button
          onClick={onReset}
          style={{
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
            padding: "8px 20px",
            color: "#F0F0F5",
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: 13,
            cursor: "pointer",
          }}
        >
          Review cards again
        </button>
        <button
          onClick={() => window.location.href = "/saved"}
          style={{
            background: "rgba(0,212,170,0.08)",
            border: "1px solid rgba(0,212,170,0.2)",
            borderRadius: 8,
            padding: "8px 20px",
            color: "#00D4AA",
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: 13,
            cursor: "pointer",
          }}
        >
          View saved cards
        </button>
      </div>
    </div>
  );
}
