import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Upload from "./pages/Upload";
import Gastos from "./pages/Gastos";
import Chat from "./pages/Chat";
import Monitor from "./pages/Monitor";
import Login from "./pages/Login";

function ProtectedRoute({ children }) {
  const user = localStorage.getItem("expensr_user");

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function LoginRoute() {
  const user = localStorage.getItem("expensr_user");

  if (user) {
    return <Navigate to="/upload" replace />;
  }

  return <Login />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginRoute />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/upload" replace />} />
          <Route path="upload" element={<Upload />} />
          <Route path="gastos" element={<Gastos />} />
          <Route path="chat" element={<Chat />} />
          <Route path="monitor" element={<Monitor />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
