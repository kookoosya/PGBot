import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import { PublicLayout } from "./components/layout/PublicLayout";
import { useAuth } from "./lib/auth";
import { AIChat } from "./pages/AIChat";
import { Analytics } from "./pages/Analytics";
import { AuditLogs } from "./pages/AuditLogs";
import { Dashboard } from "./pages/Dashboard";
import { Departments } from "./pages/Departments";
import { Issues } from "./pages/Issues";
import { Landing } from "./pages/Landing";
import { MapPage } from "./pages/Map";
import { Services } from "./pages/Services";
import { ServiceRegister } from "./pages/ServiceRegister";
import { Classifieds } from "./pages/Classifieds";
import { ProviderCabinet } from "./pages/ProviderCabinet";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Residents } from "./pages/Residents";
import { Settings } from "./pages/Settings";
import { Verification } from "./pages/Verification";

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex h-screen items-center justify-center">Загрузка...</div>;
  if (!user) return <Navigate to="/admin/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<Landing />} />
        <Route path="ai" element={<AIChat />} />
        <Route path="map" element={<MapPage />} />
        <Route path="services" element={<Services />} />
        <Route path="services/register" element={<ServiceRegister />} />
        <Route path="services/cabinet" element={<ProviderCabinet />} />
        <Route path="classifieds" element={<Classifieds />} />
        <Route path="register" element={<Register />} />
      </Route>

      <Route path="/admin/login" element={<Login />} />

      <Route
        path="/admin"
        element={
          <AdminRoute>
            <Layout />
          </AdminRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="issues" element={<Issues />} />
        <Route path="residents" element={<Residents />} />
        <Route path="departments" element={<Departments />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="audit" element={<AuditLogs />} />
        <Route path="verification" element={<Verification />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      <Route path="/login" element={<Navigate to="/admin/login" replace />} />
    </Routes>
  );
}
