/** Классы сетки главной в зависимости от количества элементов */
export function landingGridCountClass(count: number, prefix: string): string {
  if (count <= 0) return "";
  const capped = Math.min(count, 3);
  return `${prefix}--count-${capped}`;
}
