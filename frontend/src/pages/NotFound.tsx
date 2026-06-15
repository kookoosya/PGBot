import { Link } from "react-router-dom";
import { LiteraryEmptyState } from "@/components/literary";
import { EMPTY_STATES } from "@/lib/literaryCopy";

export function NotFound() {
  return (
    <div className="literary-page page-section max-w-lg mx-auto py-12">
      <LiteraryEmptyState {...EMPTY_STATES.notFound}>
        <div className="landing-inline-actions flex flex-wrap gap-3 justify-center mt-4">
          <Link to="/" className="literary-btn literary-btn--primary no-underline">
            На главную
          </Link>
          <Link to="/map" className="literary-btn literary-btn--ghost no-underline">
            Карта
          </Link>
          <Link to="/events" className="literary-btn literary-btn--ghost no-underline">
            Афиша
          </Link>
        </div>
      </LiteraryEmptyState>
    </div>
  );
}
