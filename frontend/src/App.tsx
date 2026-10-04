import { Navigate, Route, Routes } from "react-router-dom";
import Badges from "./pages/Badges";
import Diagnostic from "./pages/Diagnostic";
import Landing from "./pages/Landing";
import LearnEntry from "./pages/LearnEntry";
import Login from "./pages/Login";
import ParentDashboard from "./pages/ParentDashboard";
import ParentSettings from "./pages/ParentSettings";
import PracticePass from "./pages/PracticePass";
import Privacy from "./pages/Privacy";
import SkillMap from "./pages/SkillMap";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/practice/:token" element={<PracticePass />} />
      <Route path="/learn" element={<LearnEntry />} />
      <Route path="/parent" element={<ParentDashboard />} />
      <Route path="/parent/settings" element={<ParentSettings />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/diagnostic/:sessionId" element={<Diagnostic />} />
      <Route path="/learn/:sessionId" element={<Workspace />} />
      <Route path="/learn/:sessionId/badges" element={<Badges />} />
      <Route path="/learn/:sessionId/map" element={<SkillMap />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
