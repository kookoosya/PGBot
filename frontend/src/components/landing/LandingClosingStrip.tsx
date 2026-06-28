import { Link } from "react-router-dom";

export function LandingClosingStrip() {
  return (
    <footer className="landing-closing" aria-label="О посёлке">
      <p className="landing-closing-verse">
        Михайловское · Святогорье · живое Пушкиногорье
      </p>
      <Link to="/map" className="landing-closing-link">
        Открыть карту посёлка →
      </Link>
    </footer>
  );
}
