import { Link } from "react-router-dom";
import type { EventCardEvent } from "@/lib/eventUtils";
import {
  extractEventTimeLabel,
  groupFestivalPerformancesByDay,
  shortenFestivalPerformanceTitle,
} from "@/lib/eventUtils";

interface FestivalProgramScheduleProps {
  events: EventCardEvent[];
  eventQuerySuffix?: string;
}

export function FestivalProgramSchedule({ events, eventQuerySuffix = "" }: FestivalProgramScheduleProps) {
  const days = groupFestivalPerformancesByDay(events);

  return (
    <div className="events-festival-schedule">
      {days.map((day) => (
        <section key={day.dayKey} className="events-festival-schedule__day">
          <h4 className="events-festival-schedule__day-title">{day.dayLabel}</h4>
          <ol className="events-festival-schedule__list">
            {day.items.map((event) => (
              <li key={event.id} className="events-festival-schedule__item">
                <time className="events-festival-schedule__time">{extractEventTimeLabel(event)}</time>
                <Link to={`/events/${event.id}${eventQuerySuffix}`} className="events-festival-schedule__title">
                  {shortenFestivalPerformanceTitle(event.title)}
                </Link>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}
