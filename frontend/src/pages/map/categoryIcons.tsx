import { createElement, type CSSProperties } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  Building2,
  Bus,
  CarTaxiFront,
  CircleDot,
  Coffee,
  Cog,
  Fuel,
  Hotel,
  Hospital,
  Landmark,
  Library,
  Mailbox,
  MapPin,
  PawPrint,
  Pill,
  School,
  Scissors,
  ShoppingBasket,
  SquareParking,
  Store,
  Truck,
  Utensils,
  Waves,
  Wrench,
  type LucideIcon,
} from "lucide-react";

/** Slugs aligned with backend PlaceCategory plus upcoming auto categories. */
export const PLACE_CATEGORY_SLUGS = [
  "shop",
  "supermarket",
  "pharmacy",
  "cafe",
  "restaurant",
  "bank",
  "post",
  "school",
  "hospital",
  "vet",
  "government",
  "transport",
  "culture",
  "hotel",
  "rental",
  "gas",
  "beauty",
  "tyre",
  "auto",
  "taxi",
  "parking",
  "car_wash",
  "auto_parts",
  "towing",
  "other",
] as const;

export type PlaceCategorySlug = (typeof PLACE_CATEGORY_SLUGS)[number];

export const CATEGORY_ICON_COMPONENTS: Record<PlaceCategorySlug, LucideIcon> = {
  shop: ShoppingBasket,
  supermarket: Store,
  pharmacy: Pill,
  cafe: Coffee,
  restaurant: Utensils,
  bank: Landmark,
  post: Mailbox,
  school: School,
  hospital: Hospital,
  vet: PawPrint,
  government: Building2,
  transport: Bus,
  culture: Library,
  hotel: Hotel,
  rental: Hotel,
  gas: Fuel,
  beauty: Scissors,
  tyre: CircleDot,
  auto: Wrench,
  taxi: CarTaxiFront,
  parking: SquareParking,
  car_wash: Waves,
  auto_parts: Cog,
  towing: Truck,
  other: MapPin,
};

export function getCategoryIconComponent(category: string): LucideIcon {
  return CATEGORY_ICON_COMPONENTS[category as PlaceCategorySlug] ?? MapPin;
}

type CategoryIconProps = {
  category: string;
  size?: number;
  className?: string;
  style?: CSSProperties;
  color?: string;
};

export function CategoryIcon({
  category,
  size = 15,
  className,
  style,
  color,
}: CategoryIconProps) {
  const Icon = getCategoryIconComponent(category);
  return (
    <Icon
      className={className}
      size={size}
      strokeWidth={1.8}
      aria-hidden
      style={color ? { ...style, color } : style}
    />
  );
}

/** Static SVG markup for Leaflet divIcon (controlled category slugs only). */
export function categoryIconMarkup(
  category: string,
  size = 17,
  color = "currentColor",
): string {
  const Icon = getCategoryIconComponent(category);
  return renderToStaticMarkup(
    createElement(Icon, {
      size,
      strokeWidth: 1.8,
      color,
      "aria-hidden": true,
      className: "map-marker-icon-svg",
    }),
  );
}
