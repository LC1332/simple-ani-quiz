import { Navigate, Route, Routes } from "react-router-dom";
import ExplorePage from "./pages/ExplorePage";
import HomePage from "./pages/HomePage";
import QuizPage from "./pages/QuizPage";
import ReportPage from "./pages/ReportPage";
import StartPage from "./pages/StartPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/start/:level" element={<StartPage />} />
      <Route path="/quiz/:level" element={<QuizPage />} />
      <Route path="/report/:level" element={<ReportPage />} />
      <Route path="/explore" element={<ExplorePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
