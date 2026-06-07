import { cn } from "@/lib/utils";
import {
  BarChart3,
  Building2,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "@/lib/auth";

const navItems = [
  { to: "/admin", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/admin/issues", icon: ClipboardList, label: "Обращения" },
  { to: "/admin/residents", icon: Users, label: "Жители" },
  { to: "/admin/departments", icon: Building2, label: "Отделы" },
  { to: "/admin/analytics", icon: BarChart3, label: "Аналитика" },
  { to: "/admin/verification", icon: ShieldCheck, label: "Верификация" },
  { to: "/admin/audit", icon: FileText, label: "Аудит" },
  { to: "/admin/settings", icon: Settings, label: "Настройки" },
];

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-screen w-64 flex-col border-r pushkin-gradient text-white">
      <div className="border-b border-white/10 p-6">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-2xl">🪶</span>
          <div>
            <h1 className="text-lg font-bold leading-tight">Народный Контроль</h1>
            <p className="text-xs text-white/60">Пушкинские Горы</p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/admin"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-amber-500/20 text-amber-300"
                  : "text-white/70 hover:bg-white/10 hover:text-white"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="mb-3 px-3">
          <p className="text-sm font-medium">{user?.full_name || user?.username}</p>
          <p className="text-xs text-white/50">{user?.role}</p>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-white/60 hover:bg-white/10"
        >
          <LogOut className="h-4 w-4" />
          Выйти
        </button>
      </div>
    </aside>
  );
}
