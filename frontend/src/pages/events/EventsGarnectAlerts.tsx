import { Link } from "react-router-dom";

import type { PublicEvent } from "@/lib/api/types/events";
import { formatFestivalDateRange, isFestivalImminent, isFestivalPast } from "@/lib/eventUtils";

type EventsGarnectAlertsProps = {
  eventsBase: string;
  garnectOnly: boolean;
  garnectProgram: PublicEvent[];
};

export function EventsGarnectAlerts({ eventsBase, garnectOnly, garnectProgram }: EventsGarnectAlertsProps) {
  if (!garnectOnly || garnectProgram.length === 0) return null;

  if (isFestivalImminent(garnectProgram)) {
    return (
      <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
        <p className="font-medium">Фестиваль «Гарнец» — {formatFestivalDateRange(garnectProgram)}</p>
        <p className="mt-1 text-amber-900/90">
          Программа на двух площадках: Пушкинские Горы и Пушкинский заповедник. Ниже — спектакли по датам.
        </p>
      </div>
    );
  }

  if (isFestivalPast(garnectProgram)) {
    return (
      <div className="mb-4 rounded-xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-800">
        <p className="font-medium">Фестиваль «Гарнец» завершился</p>
        <p className="mt-1 text-stone-700">
          Ниже — архивная программа. Актуальная афиша —{" "}
          <Link to={eventsBase} className="font-medium text-primary-700 underline-offset-2 hover:underline">
            все события
          </Link>
          .
        </p>
      </div>
    );
  }

  return null;
}
