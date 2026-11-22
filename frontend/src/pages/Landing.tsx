import { TireServiceLanding } from "@/components/tire/TireServiceLanding";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";

export function Landing() {
  useDocumentTitle("Шиномонтаж и портал посёлка");
  return <TireServiceLanding />;
}
