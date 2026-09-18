import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Upload from "./pages/Upload";
import Gastos from "./pages/Gastos";
import Chat from "./pages/Chat";
import Monitor from "./pages/Monitor";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/upload" replace />} />
          <Route path="upload" element={<Upload />} />
          <Route path="gastos" element={<Gastos />} />
          <Route path="chat" element={<Chat />} />
          <Route path="monitor" element={<Monitor />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;