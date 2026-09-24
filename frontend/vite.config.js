import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev mode (npm run dev): /api aur /ws requests backend (port 8000) pe forward hoti hain.
// Isse CORS ki tension nahi rehti aur frontend code mein URL hardcode nahi karna padta.
const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  build: { chunkSizeWarningLimit: 4000 }, // Monaco editor bada hai, yeh normal hai
  server: {
    port: 5173,
    proxy: {
      "/api": BACKEND,
      "/ws": { target: BACKEND.replace("http", "ws"), ws: true },
    },
  },
});
