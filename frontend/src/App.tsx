import { Navigate, Route, Routes } from "react-router-dom";
import Badges from "./pages/Badges";
import LearnEntry from "./pages/LearnEntry";
import Login from "./pages/Login";
import SkillMap from "./pages/SkillMap";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/learn" element={<LearnEntry />} />
      <Route path="/learn/:sessionId" element={<Workspace />} />
      <Route path="/learn/:sessionId/badges" element={<Badges />} />
      <Route path="/learn/:sessionId/map" element={<SkillMap />} />
      <Route path="*" element={<Navigate to="/learn" replace />} />
    </Routes>
  );
}
