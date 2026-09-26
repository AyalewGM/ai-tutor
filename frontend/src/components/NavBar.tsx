import { Link, useLocation, useNavigate } from "react-router-dom";
import { post } from "../api";

export default function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();

  async function signOut() {
    try { await post("/auth/logout"); } catch { /* best effort */ }
    navigate("/login");
  }

  const active = (path: string) => location.pathname.startsWith(path);

  return (
    <header className="navbar">
      <Link to="/learn" className="brand" aria-label="AI Tutor home">
        <span className="brand-mark" aria-hidden="true">A</span>
        <span className="brand-label">AI Tutor</span>
      </Link>
      <nav aria-label="Primary navigation">
        <Link to="/learn" aria-current={active("/learn") ? "page" : undefined}>Practice</Link>
        <Link to="/parent" aria-current={active("/parent") ? "page" : undefined}>Parent</Link>
        <button className="linklike" onClick={signOut}>Sign out</button>
      </nav>
    </header>
  );
}
