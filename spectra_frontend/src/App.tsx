import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { Start } from "./pages/Start";
import { Mission } from "./pages/Mission";
import { Debrief } from "./pages/Debrief";
import "./adaptive/theme.css";

export default function App() {
  return (
    // runtimeUrl points to the Vite-hosted CopilotKit runtime (vite.config.ts plugin)
    <CopilotKit runtimeUrl="/copilotkit">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Start />} />
          <Route path="/debrief/:sessionId" element={<Debrief />} />
          <Route path="/mission/:sessionId" element={<Mission />} />
        </Routes>
      </BrowserRouter>
    </CopilotKit>
  );
}
