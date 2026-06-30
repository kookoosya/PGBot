import { NavLink } from "react-router-dom";
import { CLASSIFIED_BOARDS } from "@/lib/classifiedBoard";

export function ClassifiedBoardTabs() {
  return (
    <nav className="classified-board-tabs" aria-label="Разделы доски объявлений">
      {CLASSIFIED_BOARDS.map((board) => (
        <NavLink
          key={board.id}
          to={board.path}
          end={board.id === "all"}
          className={({ isActive }) =>
            `classified-board-tab${isActive ? " classified-board-tab--active" : ""}`
          }
        >
          <span className="classified-board-tab-icon" aria-hidden>
            {board.icon}
          </span>
          <span className="classified-board-tab-label">{board.title}</span>
        </NavLink>
      ))}
    </nav>
  );
}
