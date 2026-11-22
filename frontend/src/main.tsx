import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./lib/auth";
import { UserAuthProvider } from "./lib/userAuth";
import "@fontsource/playfair-display/600.css";
import "@fontsource/playfair-display/500.css";
import "@fontsource/playfair-display/500-italic.css";
import "@fontsource/playfair-display/700.css";
import "@fontsource/source-serif-4/400.css";
import "@fontsource/source-sans-3/400.css";
import "@fontsource/source-sans-3/600.css";
import "./index.css";
import "./styles/literary-album/index.css";

const root = document.getElementById("root")!;
const app = (
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <UserAuthProvider>
          <App />
        </UserAuthProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);

if (window.location.pathname === "/" && root.hasAttribute("data-prerendered")) {
  ReactDOM.hydrateRoot(root, app);
} else {
  ReactDOM.createRoot(root).render(app);
}
