import { useGetPipelineLogs, getGetPipelineLogsQueryKey } from "@workspace/api-client-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertCircle, CheckCircle2, Clock, Loader2 } from "lucide-react";

export default function Pipeline() {
  const { data: logsData, isLoading } = useGetPipelineLogs({ limit: 50 }, {
    query: { queryKey: getGetPipelineLogsQueryKey({ limit: 50 }) }
  });
  const logs = Array.isArray(logsData) ? logsData : (logsData as any)?.logs ?? [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle2 className="w-4 h-4 text-chart-1" />;
      case 'failed': return <AlertCircle className="w-4 h-4 text-destructive" />;
      case 'running': return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
      default: return <Clock className="w-4 h-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="p-6 md:p-8 flex flex-col h-full gap-6">
      <header>
        <h1 className="text-3xl font-display font-bold tracking-tight">Pipeline Logs</h1>
        <p className="text-muted-foreground text-sm">System diagnostic and processing history</p>
      </header>

      <div className="bg-card border border-border rounded-xl overflow-hidden flex-1 overflow-y-auto custom-scrollbar">
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-muted/50 sticky top-0">
              <TableRow>
                <TableHead className="font-mono text-xs">STATUS</TableHead>
                <TableHead className="font-mono text-xs">STAGE</TableHead>
                <TableHead className="font-mono text-xs text-right">PROCESSED</TableHead>
                <TableHead className="font-mono text-xs text-right">FAILED</TableHead>
                <TableHead className="font-mono text-xs">STARTED</TableHead>
                <TableHead className="font-mono text-xs">COMPLETED</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground font-mono text-sm">
                    NO PIPELINE LOGS FOUND
                  </TableCell>
                </TableRow>
              )}
              {logs?.map((log: any) => (
                <TableRow key={log.id} className="hover:bg-muted/50">
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(log.status)}
                      <span className="font-mono text-xs uppercase">{log.status}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="font-mono text-[10px] bg-background">
                      {log.stage.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-chart-1">
                    {log.items_processed > 0 ? `+${log.items_processed}` : '-'}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-destructive">
                    {log.items_failed > 0 ? log.items_failed : '-'}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {log.started_at ? new Date(log.started_at).toLocaleTimeString() : '-'}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {log.completed_at ? new Date(log.completed_at).toLocaleTimeString() : '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}