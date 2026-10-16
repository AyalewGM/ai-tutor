import { Link, useLocation, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { post } from "../api";
import Brand from "./Brand";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();

  async function signOut() {
    try { await post("/auth/logout"); } catch { /* best effort */ }
    navigate("/login");
  }

  const active = (path: string) => location.pathname.startsWith(path);

  const navLink = (path: string, label: string) => (
    <Link
      to={path}
      aria-current={active(path) ? "page" : undefined}
      className={cn(
        "rounded-md px-3 py-2 text-sm font-medium transition-colors",
        active(path)
          ? "bg-secondary text-secondary-foreground"
          : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
      )}
    >
      {label}
    </Link>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex min-h-14 max-w-6xl flex-wrap items-center gap-2 px-4 py-2 sm:gap-6">
        <Link to="/learn" className="flex items-center" aria-label="Mihur home">
          <Brand size="sm" />
        </Link>
        <nav className="order-last flex w-full items-center gap-1 sm:order-none sm:w-auto" aria-label="Primary navigation">
          {navLink("/learn", "Practice")}
          {navLink("/parent", "Parent")}
          {navLink("/together", "Together")}
        </nav>
        <div className="ml-auto">
          <Button variant="ghost" size="sm" onClick={signOut}>
            <LogOut className="mr-1.5 h-4 w-4" />
            Sign out
          </Button>
        </div>
      </div>
    </header>
  );
}
