import { cn } from "@/lib/utils";
import {
  BarChart3,
  Building2,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "@/lib/auth";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/issues", icon: ClipboardList, label: "Обращения" },
  { to: "/residents", icon: Users, label: "Жители" },
  { to: "/departments", icon: Building2, label: "Отделы" },
  { to: "/analytics", icon: BarChart3, label: "Аналитика" },
  { to: "/audit", icon: FileText, label: "Аудит" },
  { to: "/settings", icon: Settings, label: "Настройки" },
];

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-card">
      <div className="border-b p-6">
        <h1 className="text-lg font-bold leading-tight">Народный Контроль</h1>
        <p className="text-xs text-muted-foreground">Пушкинские Горы</p>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t p-4">
        <div className="mb-3 px-3">
          <p className="text-sm font-medium">{user?.full_name || user?.username}</p>
          <p className="text-xs text-muted-foreground">{user?.role}</p>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent"
        >
          <LogOut className="h-4 w-4" />
          Выйти
        </button>
      </div>
    </aside>
  );
}
