import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Explicitly load env vars from .env files in the current directory
  const env = loadEnv(mode, process.cwd(), '');
  
  // Log for debugging (remove after fixing)
  console.log('Vite config - loaded env:', {
    VITE_SUPABASE_URL: env.VITE_SUPABASE_URL,
    VITE_SUPABASE_PUBLISHABLE_KEY: env.VITE_SUPABASE_PUBLISHABLE_KEY ? 'present' : 'missing',
    mode,
    cwd: process.cwd(),
  });
  
  return {
    server: {
      host: "::",
      port: 8080,
    },
    // Removed 'lovable-tagger' plugin (was causing module not found). Re-add if installed.
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    // Tell Vite to expose VITE_ prefixed vars to import.meta.env
    envPrefix: 'VITE_',
  };
});
