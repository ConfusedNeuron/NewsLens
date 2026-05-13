import { useState } from "react";
import { useListCards, getListCardsQueryKey } from "@workspace/api-client-react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "wouter";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Card as CardType } from "@workspace/api-client-react/src/generated/api.schemas";

export default function Feed() {
  const [domain, setDomain] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  
  const params = {
    limit: 20,
    page: 1,
    ...(domain ? { domain } : {}),
    ...(search ? { search } : {}),
  };

  const { data, isLoading, error } = useListCards(
    params,
    { query: { queryKey: getListCardsQueryKey(params) } }
  );

  const domains = ["Finance", "Tech", "Geopolitics", "Environment"];

  return (
    <div className="p-6 md:p-8 flex flex-col h-full gap-6">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">Terminal Feed</h1>
          <p className="text-muted-foreground text-sm">Real-time intelligence distillation</p>
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0 max-w-full no-scrollbar">
          <button
            onClick={() => setDomain(null)}
            className={`px-3 py-1 text-xs font-mono rounded-full border transition-all ${!domain ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-muted-foreground"}`}
          >
            ALL
          </button>
          {domains.map(d => (
            <button
              key={d}
              onClick={() => setDomain(d)}
              className={`px-3 py-1 text-xs font-mono rounded-full border transition-all ${domain === d ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-muted-foreground"}`}
            >
              {d.toUpperCase()}
            </button>
          ))}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map(i => (
              <Skeleton key={i} className="h-64 rounded-xl border border-border bg-card/50" />
            ))}
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full text-destructive border border-destructive/20 bg-destructive/10 rounded-xl p-8">
            Failed to load intelligence feed. Check terminal connection.
          </div>
        ) : !data?.cards?.length ? (
          <div className="flex items-center justify-center h-full text-muted-foreground border border-border rounded-xl p-8 bg-card/50 font-mono text-sm">
            NO SIGNALS FOUND FOR CURRENT FILTERS.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <AnimatePresence>
              {data.cards.map((card: CardType, index: number) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.3 }}
                >
                  <Link href={`/card/${card.id}`} className="block h-full">
                    <div className="h-full flex flex-col p-5 rounded-xl border border-card-border bg-card hover:border-primary/50 transition-all hover:shadow-[0_0_15px_rgba(116,255,0,0.1)] group">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex gap-2 flex-wrap">
                          {card.tags?.domain?.map(d => (
                            <span key={d} className="text-[10px] font-mono uppercase text-muted-foreground bg-muted px-2 py-0.5 rounded-sm">{d}</span>
                          ))}
                        </div>
                        <Badge variant="outline" className={`text-[10px] font-mono ${card.confidence === 'high' ? 'text-primary border-primary' : card.confidence === 'medium' ? 'text-chart-4 border-chart-4' : 'text-chart-2 border-chart-2'}`}>
                          {card.confidence.toUpperCase()} CONF
                        </Badge>
                      </div>
                      
                      <h2 className="text-xl font-bold font-display leading-tight mb-2 group-hover:text-primary transition-colors">{card.headline}</h2>
                      
                      {card.key_number && (
                        <div className="text-3xl font-mono text-primary font-bold my-3 tracking-tighter">
                          {card.key_number}
                        </div>
                      )}
                      
                      <p className="text-sm text-muted-foreground line-clamp-3 mb-4 flex-1">{card.summary}</p>
                      
                      <div className="flex justify-between items-end mt-auto pt-4 border-t border-border">
                        <div className="flex gap-2">
                          {card.angles?.usa && <span className="text-sm" title="USA Impact">🇺🇸</span>}
                          {card.angles?.china && <span className="text-sm" title="China Impact">🇨🇳</span>}
                          {card.angles?.india && <span className="text-sm" title="India Impact">🇮🇳</span>}
                        </div>
                        <span className="text-xs font-mono text-muted-foreground">
                          {new Date(card.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}