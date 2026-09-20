import { Navigate, Route, Routes } from "react-router-dom";
import LearnEntry from "./pages/LearnEntry";
import Login from "./pages/Login";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/learn" element={<LearnEntry />} />
      <Route path="/learn/:sessionId" element={<Workspace />} />
      <Route path="*" element={<Navigate to="/learn" replace />} />
    </Routes>
  );
}
