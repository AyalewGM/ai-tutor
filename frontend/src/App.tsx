import { Navigate, Route, Routes } from "react-router-dom";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Badges from "./pages/Badges";
import Catalog from "./pages/Catalog";
import Diagnostic from "./pages/Diagnostic";
import Landing from "./pages/Landing";
import LearnEntry from "./pages/LearnEntry";
import Login from "./pages/Login";
import ParentDashboard from "./pages/ParentDashboard";
import ParentSettings from "./pages/ParentSettings";
import Pending from "./pages/Pending";
import PracticePass from "./pages/PracticePass";
import Privacy from "./pages/Privacy";
import SkillMap from "./pages/SkillMap";
import Unavailable from "./pages/Unavailable";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/pending" element={<Pending />} />
      <Route path="/unavailable" element={<Unavailable />} />
      <Route path="/practice/:token" element={<PracticePass />} />
      <Route path="/learn" element={<LearnEntry />} />
      <Route path="/parent" element={<ParentDashboard />} />
      <Route path="/admin" element={<AdminDashboard />} />
      <Route path="/parent/settings" element={<ParentSettings />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/diagnostic/:sessionId" element={<Diagnostic />} />
      <Route path="/learn/:sessionId" element={<Workspace />} />
      <Route path="/learn/:sessionId/badges" element={<Badges />} />
      <Route path="/learn/:sessionId/map" element={<SkillMap />} />
      <Route path="/learn/:sessionId/catalog" element={<Catalog />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
