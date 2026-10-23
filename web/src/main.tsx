import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./index.css";

// Set the theme before the first paint so dark mode doesn't flash light.
try {
  const stored = JSON.parse(localStorage.getItem("sensible.theme") ?? "null");
  const system = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  document.documentElement.dataset.theme = stored ?? system;
} catch {
  /* storage blocked: the hook falls back to the system theme */
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
