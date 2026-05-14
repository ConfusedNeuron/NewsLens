import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import { useTheme } from "@/hooks/use-theme";
import { Layout } from "@/components/layout";

import Feed from "@/pages/feed";
import CardDetail from "@/pages/card-detail";
import Sources from "@/pages/sources";
import Profile from "@/pages/profile";
import Pipeline from "@/pages/pipeline";
import SavedCards from "@/pages/saved-cards";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

function Router() {
  return (
    <Switch>
      <Route path="/" component={Feed} />
      <Route path="/card/:id">
        <Layout><CardDetail /></Layout>
      </Route>
      <Route path="/sources">
        <Layout><Sources /></Layout>
      </Route>
      <Route path="/profile">
        <Layout><Profile /></Layout>
      </Route>
      <Route path="/pipeline">
        <Layout><Pipeline /></Layout>
      </Route>
      <Route path="/saved" component={SavedCards} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  useTheme();

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
