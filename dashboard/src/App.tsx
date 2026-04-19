import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { CampaignProvider } from "./context/CampaignContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import DashboardPage from "./pages/campaign/DashboardPage";
import VotersPage from "./pages/voters/VotersPage";
import TurfsPage from "./pages/turfs/TurfsPage";
import SurveysPage from "./pages/surveys/SurveysPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CampaignProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/voters" element={<VotersPage />} />
              <Route path="/turfs" element={<TurfsPage />} />
              <Route path="/surveys" element={<SurveysPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </CampaignProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
