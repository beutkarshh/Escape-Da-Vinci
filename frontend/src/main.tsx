import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Debug: print vite runtime envs at startup. Remove after debugging.
try {
	// eslint-disable-next-line no-console
	console.info('Vite runtime env:', (import.meta as any)?.env || {});
} catch (e) {
	// ignore in production or non-vite environments
}

createRoot(document.getElementById("root")!).render(<App />);
