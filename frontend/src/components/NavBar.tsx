import { Link, useLocation, useNavigate } from "react-router-dom";
import { GraduationCap, LogOut } from "lucide-react";
import { post } from "../api";
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
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-6 px-4">
        <Link to="/learn" className="flex items-center gap-2" aria-label="AI Tutor home">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <GraduationCap className="h-4 w-4" />
          </span>
          <span className="font-bold tracking-tight">AI Tutor</span>
        </Link>
        <nav className="flex items-center gap-1" aria-label="Primary navigation">
          {navLink("/learn", "Practice")}
          {navLink("/parent", "Parent")}
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
