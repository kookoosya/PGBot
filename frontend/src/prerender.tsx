import { renderToString } from "react-dom/server";
import { Route, Routes } from "react-router-dom";
import { StaticRouter } from "react-router-dom/server";
import { PublicLayout } from "./components/layout/PublicLayout";
import { UserAuthProvider } from "./lib/userAuth";
import { Landing } from "./pages/Landing";
import { TIRE_SERVICE } from "./lib/tireService";

export function renderHome() {
  return renderToString(
    <StaticRouter location="/">
      <UserAuthProvider>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route index element={<Landing />} />
          </Route>
        </Routes>
      </UserAuthProvider>
    </StaticRouter>,
  );
}

export function getHomeStructuredData(url: string) {
  return {
    "@context": "https://schema.org",
    "@type": "AutoRepair",
    name: TIRE_SERVICE.name,
    url,
    telephone: TIRE_SERVICE.phoneHref.slice(4),
    address: TIRE_SERVICE.address,
  };
}
