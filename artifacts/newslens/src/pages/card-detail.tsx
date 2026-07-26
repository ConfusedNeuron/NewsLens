import { useParams, Link } from "wouter";
import { useGetCard, getGetCardQueryKey, useSwipeCard } from "@workspace/api-client-react";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";

/**
 * Magnitude with provenance. Mirrors ImpactRow in NewsCard.tsx: figures the model
 * inferred rather than read from the enrichment payload are labelled and demoted,
 * so a reader can tell which numbers are sourced. Unlabelled means estimate.
 * The detail page previously dropped `magnitude` altogether.
 */
function Magnitude({ item }: { item: any }) {
  if (!item?.magnitude) return null;
  const isSourced = item.magnitude_source === "data";
  return (
    <span
      className={`block mt-1 text-xs ${isSourced ? "text-muted-foreground" : "text-muted-foreground/60 italic"}`}
      title={
        isSourced
          ? "Figure taken from market data or from the source article."
          : "Model estimate — not from a verified data source."
      }
    >
      {!isSourced && (
        <span
          className="not-italic mr-1.5 rounded border border-border px-1 py-px text-[9px] font-bold uppercase tracking-wide"
          aria-label="Model estimate, not from a verified data source"
        >
          est
        </span>
      )}
      {item.magnitude}
    </span>
  );
}

export default function CardDetail() {
  const params = useParams();
  const id = params.id as string;

  const { data: card, isLoading } = useGetCard(id, {
    query: { enabled: !!id, queryKey: getGetCardQueryKey(id) }
  });

  const swipeCard = useSwipeCard();

  const handleSwipe = (direction: "left" | "right") => {
    swipeCard.mutate({ id, data: { direction, user_id: "default_user" } });
  };

  if (isLoading) {
    return (
      <div className="p-8 max-w-3xl mx-auto space-y-6">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-64 w-full rounded-xl" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    );
  }

  if (!card) {
    return <div className="p-8 text-center text-muted-foreground font-mono">CARD NOT FOUND</div>;
  }

  return (
    <div className="p-6 md:p-8 max-w-3xl mx-auto min-h-full flex flex-col pb-24">
      <Link href="/" className="inline-flex items-center gap-2 text-sm font-mono text-muted-foreground hover:text-primary transition-colors mb-6 w-fit">
        <ArrowLeft className="w-4 h-4" /> BACK TO FEED
      </Link>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        <div className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            {card.tags?.domain?.map((d: string) => (
              <span key={d} className="text-xs font-mono uppercase text-muted-foreground bg-muted px-2 py-1 rounded-sm">{d}</span>
            ))}
            <Badge variant="outline" className={`text-xs font-mono ml-auto ${card.confidence === 'high' ? 'text-primary border-primary' : 'text-muted-foreground'}`}>
              {card.confidence.toUpperCase()} CONFIDENCE
            </Badge>
          </div>
          
          <h1 className="text-3xl md:text-5xl font-display font-bold leading-tight">{card.headline}</h1>
          
          {card.key_number && (
            <div className="text-5xl md:text-7xl font-mono text-primary font-bold py-4 tracking-tighter">
              {card.key_number}
            </div>
          )}
          
          <div className="text-lg text-muted-foreground leading-relaxed border-l-2 border-primary pl-4">
            {card.summary}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {card.winners && card.winners.length > 0 && (
            <div className="bg-card border border-card-border rounded-xl p-5 shadow-sm">
              <h3 className="font-mono text-sm text-chart-1 mb-4 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-chart-1" /> WINNERS
              </h3>
              <ul className="space-y-4">
                {card.winners.map((w: any, i: number) => (
                  <li key={i} className="text-sm">
                    <span className="font-bold block text-foreground">{w.who}</span>
                    <span className="text-muted-foreground">{w.why}</span>
                    <Magnitude item={w} />
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {card.losers && card.losers.length > 0 && (
            <div className="bg-card border border-card-border rounded-xl p-5 shadow-sm">
              <h3 className="font-mono text-sm text-chart-2 mb-4 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-chart-2" /> LOSERS
              </h3>
              <ul className="space-y-4">
                {card.losers.map((l: any, i: number) => (
                  <li key={i} className="text-sm">
                    <span className="font-bold block text-foreground">{l.who}</span>
                    <span className="text-muted-foreground">{l.why}</span>
                    <Magnitude item={l} />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {card.angles && Object.keys(card.angles).length > 0 && (
          <div className="space-y-4">
            <h3 className="font-mono text-sm text-muted-foreground border-b border-border pb-2">GEO ANGLES</h3>
            <div className="grid gap-4">
              {card.angles.usa && (
                <div className="flex gap-4 p-4 rounded-lg bg-secondary/50">
                  <span className="text-2xl">🇺🇸</span>
                  <p className="text-sm leading-relaxed">{card.angles.usa}</p>
                </div>
              )}
              {card.angles.china && (
                <div className="flex gap-4 p-4 rounded-lg bg-secondary/50">
                  <span className="text-2xl">🇨🇳</span>
                  <p className="text-sm leading-relaxed">{card.angles.china}</p>
                </div>
              )}
              {card.angles.india && (
                <div className="flex gap-4 p-4 rounded-lg bg-secondary/50">
                  <span className="text-2xl">🇮🇳</span>
                  <p className="text-sm leading-relaxed">{card.angles.india}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {card.personal_impact && (
          <div className="bg-primary/10 border border-primary/20 rounded-xl p-6">
            <h3 className="font-mono text-sm text-primary mb-2">PERSONAL IMPACT</h3>
            <p className="text-sm leading-relaxed">{card.personal_impact}</p>
          </div>
        )}

        <div className="flex items-center justify-between pt-8 border-t border-border mt-8">
          <div className="text-xs font-mono text-muted-foreground">
            {new Date(card.created_at).toLocaleString()}
          </div>
          {card.source && (
            <a href={card.source.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-xs font-mono text-primary hover:underline">
              SOURCE: {card.source.name} <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </motion.div>

      {/* Fixed Swipe Controls */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-background/80 backdrop-blur-md px-6 py-3 rounded-full border border-border shadow-xl">
        <button 
          onClick={() => handleSwipe("left")}
          className="flex items-center gap-2 text-chart-2 hover:text-chart-2/80 font-mono text-sm transition-colors"
          disabled={swipeCard.isPending}
        >
          <ChevronLeft className="w-5 h-5" /> PASS
        </button>
        <div className="w-px h-6 bg-border" />
        <button 
          onClick={() => handleSwipe("right")}
          className="flex items-center gap-2 text-chart-1 hover:text-chart-1/80 font-mono text-sm transition-colors"
          disabled={swipeCard.isPending}
        >
          SAVE <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}