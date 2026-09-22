import { Link, useNavigate } from "react-router-dom";
import { post } from "../api";

export default function NavBar() {
  const navigate = useNavigate();

  async function signOut() {
    try {
      await post("/auth/logout");
    } catch {
      /* best effort */
    }
    navigate("/login");
  }

  return (
    <header className="navbar">
      <Link to="/learn" className="brand">
        AI Tutor
      </Link>
      <nav>
        <Link to="/learn">Practice</Link>
        <Link to="/parent">Parent</Link>
        <button className="linklike" onClick={signOut}>
          Sign out
        </button>
      </nav>
    </header>
  );
}
