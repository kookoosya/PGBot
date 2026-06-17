export function eventSharePath(eventId: number): string {
  return `/share/events/${eventId}`;
}

export function absoluteEventShareUrl(origin: string, eventId: number): string {
  return `${origin.replace(/\/$/, "")}${eventSharePath(eventId)}`;
}
