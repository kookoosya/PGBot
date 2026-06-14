import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { PageLoader } from "./components/PageLoader";
import { Layout } from "./components/layout/Layout";
import { PublicLayout } from "./components/layout/PublicLayout";
import { useAuth } from "./lib/auth";
import { isOfficialUser, useUserAuth } from "./lib/userAuth";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { RegisterHub } from "./pages/RegisterHub";
import { UserLogin } from "./pages/UserLogin";
import { NotFound } from "./pages/NotFound";

const MapPage = lazy(() => import("./pages/Map").then((m) => ({ default: m.MapPage })));
const AIChat = lazy(() => import("./pages/AIChat").then((m) => ({ default: m.AIChat })));
const Services = lazy(() => import("./pages/Services").then((m) => ({ default: m.Services })));
const ServiceRegister = lazy(() => import("./pages/ServiceRegister").then((m) => ({ default: m.ServiceRegister })));
const Classifieds = lazy(() => import("./pages/Classifieds").then((m) => ({ default: m.Classifieds })));
const Jobs = lazy(() => import("./pages/Jobs").then((m) => ({ default: m.Jobs })));
const EventsPage = lazy(() => import("./pages/EventsPage").then((m) => ({ default: m.EventsPage })));
const EventDetail = lazy(() => import("./pages/EventDetail").then((m) => ({ default: m.EventDetail })));
const ClassifiedDetail = lazy(() => import("./pages/ClassifiedDetail").then((m) => ({ default: m.ClassifiedDetail })));
const Complaints = lazy(() => import("./pages/Complaints").then((m) => ({ default: m.Complaints })));
const OfficialIssues = lazy(() => import("./pages/OfficialIssues").then((m) => ({ default: m.OfficialIssues })));
const ProviderCabinet = lazy(() => import("./pages/ProviderCabinet").then((m) => ({ default: m.ProviderCabinet })));
const Register = lazy(() => import("./pages/Register").then((m) => ({ default: m.Register })));
const RegisterOrganization = lazy(() => import("./pages/RegisterOrganization").then((m) => ({ default: m.RegisterOrganization })));
const Signup = lazy(() => import("./pages/Signup").then((m) => ({ default: m.Signup })));
const UserCabinet = lazy(() => import("./pages/UserCabinet").then((m) => ({ default: m.UserCabinet })));
const Dashboard = lazy(() => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })));
const Issues = lazy(() => import("./pages/Issues").then((m) => ({ default: m.Issues })));
const Residents = lazy(() => import("./pages/Residents").then((m) => ({ default: m.Residents })));
const Departments = lazy(() => import("./pages/Departments").then((m) => ({ default: m.Departments })));
const Analytics = lazy(() => import("./pages/Analytics").then((m) => ({ default: m.Analytics })));
const AdminMarketing = lazy(() => import("./pages/AdminMarketing").then((m) => ({ default: m.AdminMarketing })));
const AdminVisits = lazy(() => import("./pages/AdminVisits").then((m) => ({ default: m.AdminVisits })));
const Verification = lazy(() => import("./pages/Verification").then((m) => ({ default: m.Verification })));
const ClassifiedModeration = lazy(() => import("./pages/ClassifiedModeration").then((m) => ({ default: m.ClassifiedModeration })));
const AdminProposals = lazy(() => import("./pages/AdminProposals").then((m) => ({ default: m.AdminProposals })));
const Wishes = lazy(() => import("./pages/Wishes").then((m) => ({ default: m.Wishes })));
const AdminFeedback = lazy(() => import("./pages/AdminFeedback").then((m) => ({ default: m.AdminFeedback })));
const AuditLogs = lazy(() => import("./pages/AuditLogs").then((m) => ({ default: m.AuditLogs })));
const Settings = lazy(() => import("./pages/Settings").then((m) => ({ default: m.Settings })));

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isOwner, loading } = useAuth();
  if (loading) return <div className="flex h-screen items-center justify-center">Загрузка...</div>;
  if (!user || !isOwner) return <Navigate to="/admin/login" replace />;
  return <>{children}</>;
}

function UserRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useUserAuth();
  if (loading) return <div className="page-section text-center text-muted-foreground">Загрузка...</div>;
  if (!user) return <Navigate to="/cabinet/login" replace />;
  return <>{children}</>;
}

function OfficialRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useUserAuth();
  if (loading) return <div className="page-section text-center text-muted-foreground">Загрузка...</div>;
  if (!user) return <Navigate to="/cabinet/login?next=/official" replace />;
  if (!isOfficialUser(user)) return <Navigate to="/cabinet" replace />;
  return <>{children}</>;
}

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<Landing />} />
        <Route path="ai" element={<Lazy><AIChat /></Lazy>} />
        <Route path="map" element={<Lazy><MapPage /></Lazy>} />
        <Route path="services" element={<Lazy><Services /></Lazy>} />
        <Route path="services/register" element={<Lazy><ServiceRegister /></Lazy>} />
        <Route path="services/cabinet" element={<Lazy><ProviderCabinet /></Lazy>} />
        <Route path="classifieds" element={<Lazy><Classifieds /></Lazy>} />
        <Route path="classifieds/:id" element={<Lazy><ClassifiedDetail /></Lazy>} />
        <Route path="jobs" element={<Lazy><Jobs /></Lazy>} />
        <Route path="events" element={<Lazy><EventsPage /></Lazy>} />
        <Route path="events/:id" element={<Lazy><EventDetail /></Lazy>} />
        <Route path="complaints" element={<Lazy><Complaints /></Lazy>} />
        <Route path="wishes" element={<Lazy><Wishes /></Lazy>} />
        <Route path="register" element={<RegisterHub />} />
        <Route path="signup" element={<Lazy><Signup /></Lazy>} />
        <Route path="register/organization" element={<Lazy><RegisterOrganization /></Lazy>} />
        <Route path="register/official" element={<Lazy><Register /></Lazy>} />
        <Route path="cabinet/login" element={<UserLogin />} />
        <Route
          path="cabinet"
          element={
            <UserRoute>
              <Lazy><UserCabinet /></Lazy>
            </UserRoute>
          }
        />
        <Route
          path="official"
          element={
            <OfficialRoute>
              <Lazy><OfficialIssues /></Lazy>
            </OfficialRoute>
          }
        />
        <Route path="*" element={<NotFound />} />
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
        <Route index element={<Lazy><Dashboard /></Lazy>} />
        <Route path="issues" element={<Lazy><Issues /></Lazy>} />
        <Route path="residents" element={<Lazy><Residents /></Lazy>} />
        <Route path="departments" element={<Lazy><Departments /></Lazy>} />
        <Route path="analytics" element={<Lazy><Analytics /></Lazy>} />
        <Route path="marketing" element={<Lazy><AdminMarketing /></Lazy>} />
        <Route path="visits" element={<Lazy><AdminVisits /></Lazy>} />
        <Route path="verification" element={<Lazy><Verification /></Lazy>} />
        <Route path="classifieds" element={<Lazy><ClassifiedModeration /></Lazy>} />
        <Route path="proposals" element={<Lazy><AdminProposals /></Lazy>} />
        <Route path="feedback" element={<Lazy><AdminFeedback /></Lazy>} />
        <Route path="audit" element={<Lazy><AuditLogs /></Lazy>} />
        <Route path="settings" element={<Lazy><Settings /></Lazy>} />
      </Route>

      <Route path="/login" element={<Navigate to="/cabinet/login" replace />} />
    </Routes>
  );
}
