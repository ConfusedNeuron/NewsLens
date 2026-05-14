import { Link, useLocation } from "wouter";
import { Activity, Layers, Settings, Database, Newspaper } from "lucide-react";

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  const navItems = [
    { href: "/", label: "Feed", icon: Newspaper },
    { href: "/sources", label: "Sources", icon: Database },
    { href: "/pipeline", label: "Pipeline", icon: Activity },
    { href: "/profile", label: "Profile", icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <nav className="w-16 md:w-64 border-r border-border bg-sidebar flex flex-col items-center md:items-stretch py-6 px-2 md:px-4">
        <div className="flex items-center gap-2 px-2 mb-8 text-primary">
          <Layers className="w-6 h-6" />
          <span className="hidden md:block font-display font-bold text-xl tracking-tight uppercase">NewsLens</span>
        </div>
        <div className="flex flex-col gap-2 w-full">
          {navItems.map((item) => {
            const isActive = location === item.href;
            return (
              <Link key={item.href} href={item.href} className={`flex items-center gap-3 px-2 md:px-3 py-2.5 rounded-md transition-colors ${isActive ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50"}`}>
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="hidden md:block font-medium text-sm">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-background">
        <div className="max-w-5xl mx-auto w-full h-full">
          {children}
        </div>
      </main>
    </div>
  );
}