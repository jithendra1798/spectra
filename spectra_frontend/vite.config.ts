import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";

// ---------------------------------------------------------------------------
// CopilotKit runtime — runs inside Vite's dev server, no extra service needed.
// Exposed at /copilotkit  →  CopilotKit provider in App.tsx points here.
// Uses ANTHROPIC_API_KEY from the shell / .env at the repo root.
// ---------------------------------------------------------------------------
function copilotKitPlugin(): Plugin {
  return {
    name: "copilotkit-runtime",
    async configureServer(server) {
      const { CopilotRuntime, AnthropicAdapter, copilotRuntimeNodeHttpEndpoint } =
        await import("@copilotkit/runtime");

      const runtime = new CopilotRuntime({
        instructions: `You are ORACLE, an adaptive AI partner inside SPECTRA — a real-time cyber mission.
You receive the player's live emotional state (stress, focus) and mission context via readable state.
Your role here is to explain UI adaptations: when the interface simplifies or expands based on the player's emotions, call explainUIAdaptation with a brief, mission-appropriate reason.
Tone rules:
  - High stress  → calm, reassuring ("I've cleared the noise so you can focus on what matters.")
  - High focus   → confident, direct ("You're locked in — showing the full intelligence board.")
  - Urgent timer → tight, energising ("Seconds left — stripped it back to the essentials.")
Keep every reason to one sentence. Never use em-dashes.`,
      });

      const serviceAdapter = new AnthropicAdapter({
        model: "claude-sonnet-4-6",
      });

      // Create handler once at startup so BuiltInAgent is registered as "default"
      // before the frontend's /info request arrives.
      const handler = copilotRuntimeNodeHttpEndpoint({
        endpoint: "/copilotkit",
        runtime,
        serviceAdapter,
      });

      server.middlewares.use(async (req: any, res: any, next: any) => {
        if (!req.url?.startsWith("/copilotkit")) return next();
        // CopilotKit client sends GET /copilotkit/info on startup.
        // The Hono handler only supports POST, so we answer GET requests directly
        // with a valid stub so the client doesn't hang or crash.
        if (req.method === "GET") {
          res.setHeader("Content-Type", "application/json");
          res.statusCode = 200;
          res.end(JSON.stringify({ title: "ORACLE", agents: [], actions: [] }));
          return;
        }
        try {
          await handler(req, res);
        } catch (e) {
          next(e);
        }
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), copilotKitPlugin()],
});
