import { Link } from "react-router-dom";
import { MAIN_SECTIONS, getUserHomeLabel, getUserHomePath } from "@/lib/navigation";
import { useUserAuth } from "@/lib/userAuth";

export function FooterNav() {
  const { user } = useUserAuth();

  return (
    <nav className="footer-nav" aria-label="Навигация в подвале">
      {MAIN_SECTIONS.map(({ to, label, icon }) => (
        <Link key={to} to={to} className="footer-nav-link">
          <span>{icon}</span>
          {label}
        </Link>
      ))}
      <Link to={getUserHomePath(user)} className="footer-nav-link">
        <span>👤</span>
        {user ? getUserHomeLabel(user) : "Вход"}
      </Link>
      {!user && (
        <Link to="/register" className="footer-nav-link">
          <span>✍️</span>
          Регистрация
        </Link>
      )}
    </nav>
  );
}
