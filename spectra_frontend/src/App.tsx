import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Start } from "./pages/Start";
import { Mission } from "./pages/Mission";
import { Debrief } from "./pages/Debrief";
import "./adaptive/theme.css";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Start />} />
        <Route path="/debrief/:sessionId" element={<Debrief />} />
        <Route path="/mission/:sessionId" element={<Mission />} />
      </Routes>
    </BrowserRouter>
  );
}