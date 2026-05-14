import { useGetSourcesStatus, getGetSourcesStatusQueryKey, useRunPipeline } from "@workspace/api-client-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Database, RefreshCw, CheckCircle2, XCircle, Clock } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";

export default function Sources() {
  const { data, isLoading } = useGetSourcesStatus({
    query: { queryKey: getGetSourcesStatusQueryKey() }
  });
  
  const runPipeline = useRunPipeline();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const handleRunPipeline = () => {
    runPipeline.mutate(undefined, {
      onSuccess: () => {
        toast({
          title: "Pipeline Triggered",
          description: "Ingestion and processing started in the background.",
        });
        queryClient.invalidateQueries({ queryKey: getGetSourcesStatusQueryKey() });
      },
      onError: () => {
        toast({
          title: "Pipeline Failed",
          description: "Failed to start the pipeline.",
          variant: "destructive"
        });
      }
    });
  };

  return (
    <div className="p-6 md:p-8 flex flex-col h-full gap-6">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight">Data Sources</h1>
          <p className="text-muted-foreground text-sm">Live ingestion status of 22 active sources</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-2xl font-mono font-bold text-primary">{data?.total_cards_live || 0}</div>
            <div className="text-xs text-muted-foreground font-mono">CARDS LIVE</div>
          </div>
          <Button 
            onClick={handleRunPipeline} 
            disabled={runPipeline.isPending}
            className="font-mono text-xs gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${runPipeline.isPending ? 'animate-spin' : ''}`} />
            RUN PIPELINE
          </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto pb-8 custom-scrollbar">
        {isLoading ? (
          Array(6).fill(0).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl border border-border" />)
        ) : (
          data?.sources.map((source: any, i: number) => (
            <div key={i} className="p-5 rounded-xl border border-border bg-card flex flex-col gap-4">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-muted-foreground" />
                  <span className="font-bold text-sm">{source.name}</span>
                </div>
                {source.status === 'active' || source.status === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-chart-1" />
                ) : (
                  <XCircle className="w-4 h-4 text-destructive" />
                )}
              </div>
              
              <div className="flex gap-2">
                <span className="text-[10px] font-mono uppercase bg-secondary text-secondary-foreground px-2 py-0.5 rounded-sm">
                  {source.source_type}
                </span>
                <span className="text-[10px] font-mono uppercase bg-secondary text-secondary-foreground px-2 py-0.5 rounded-sm">
                  {source.status}
                </span>
              </div>

              <div className="mt-auto pt-4 border-t border-border flex justify-between items-center text-xs font-mono text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {source.last_run ? new Date(source.last_run).toLocaleTimeString() : 'Never'}
                </div>
                <div className="text-primary font-bold">
                  +{source.items_today} TODAY
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}