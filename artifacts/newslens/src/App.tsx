import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import { useTheme } from "@/hooks/use-theme";
import { Layout } from "@/components/layout";

// Pages
import Feed from "@/pages/feed";
import CardDetail from "@/pages/card-detail";
import Sources from "@/pages/sources";
import Profile from "@/pages/profile";
import Pipeline from "@/pages/pipeline";

const queryClient = new QueryClient();

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Feed} />
        <Route path="/card/:id" component={CardDetail} />
        <Route path="/sources" component={Sources} />
        <Route path="/profile" component={Profile} />
        <Route path="/pipeline" component={Pipeline} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
  );
}

function App() {
  useTheme(); // Initializes dark mode

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
