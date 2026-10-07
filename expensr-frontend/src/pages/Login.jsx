import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const [usuario, setUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();
    setError("");

    if (usuario === "empleado_007" && password === "expensr") {
      localStorage.setItem(
        "expensr_user",
        JSON.stringify({
          empleado: "empleado_007",
          nombre: "Empleado 007",
        }),
      );

      navigate("/upload", { replace: true });
      return;
    }

    setError("Usuario o contraseña incorrectos");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white rounded-xl shadow-md p-8">
        <h1 className="text-3xl font-bold text-center mb-2">Expensr</h1>

        <p className="text-gray-500 text-center mb-8">
          Gestión empresarial de gastos
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium mb-2">
              Usuario
            </label>

            <input
              type="text"
              value={usuario}
              onChange={(event) => setUsuario(event.target.value)}
              placeholder="empleado_007"
              className="w-full border rounded-lg px-4 py-3"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Contraseña
            </label>

            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="expensr"
              className="w-full border rounded-lg px-4 py-3"
              required
            />
          </div>

          {error && (
            <p className="text-red-600 text-sm">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="w-full bg-black text-white rounded-lg py-3 font-medium hover:bg-gray-800"
          >
            Iniciar sesión
          </button>
        </form>

        <p className="text-xs text-gray-400 text-center mt-6">
          Demo · usuario: empleado_007 · contraseña: expensr
        </p>
      </div>
    </div>
  );
}

export default Login;
