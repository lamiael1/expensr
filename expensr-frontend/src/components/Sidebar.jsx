
import { NavLink, useNavigate } from "react-router-dom";

function Sidebar() {
  const navigate = useNavigate();

  const pestañas = [
    { ruta: "/upload", nombre: "Subir factura", icono: "↑" },
    { ruta: "/gastos", nombre: "Mis gastos", icono: "€" },
    { ruta: "/chat", nombre: "Preguntar", icono: "?" },
    { ruta: "/monitor", nombre: "Monitoreo", icono: "◉" },
  ];

  const user = (() => {
    try {
      return JSON.parse(localStorage.getItem("expensr_user") || "{}");
    } catch {
      return {};
    }
  })();

  const handleLogout = () => {
    localStorage.removeItem("expensr_user");
    navigate("/login", { replace: true });
  };

  return (
    <aside className="flex min-h-screen w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-950 text-white">
      {/* Logo */}
      <div className="border-b border-slate-800 px-5 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white shadow-sm">
            <span className="text-xl font-black text-slate-950">E</span>
          </div>

          <div className="min-w-0">
            <h1 className="!m-0 !text-3xl !font-extrabold !tracking-tight !text-white">
              Expensr
            </h1>
            <p className="!mt-1 !text-xs !font-medium !text-slate-300">
              Gestión de gastos
            </p>
          </div>
        </div>
      </div>

      {/* Usuario */}
      <div className="px-4 py-5">
        <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 px-3 py-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-700 font-semibold !text-white">
            {(user.nombre || "E").charAt(0).toUpperCase()}
          </div>

          <div className="min-w-0">
            <p className="truncate !text-sm !font-semibold !text-white">
              {user.nombre || "Empleado"}
            </p>
            <p className="mt-0.5 truncate !text-xs !text-slate-400">
              {user.empleado || "empleado_007"}
            </p>
          </div>
        </div>
      </div>

      {/* Navegación */}
      <nav aria-label="Navegación principal" className="flex-1 px-3">
        <p className="mb-3 px-3 !text-[11px] !font-bold uppercase !tracking-widest !text-slate-500">
          Navegación
        </p>

        <div className="space-y-1">
          {pestañas.map((p) => (
            <NavLink
              key={p.ruta}
              to={p.ruta}
              style={({ isActive }) => ({
                color: isActive ? "#ffffff" : "#cbd5e1",
                backgroundColor: isActive ? "#4f46e5" : "transparent",
              })}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-3 !no-underline transition-colors duration-150 ${
                  isActive
                    ? "font-semibold shadow-md"
                    : "font-medium hover:bg-slate-900 hover:!text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    aria-hidden="true"
                    style={{
                      color: isActive ? "#ffffff" : "#94a3b8",
                      backgroundColor: isActive ? "#4338ca" : "#0f172a",
                    }}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg font-bold"
                  >
                    {p.icono}
                  </span>

                  <span
                    style={{ color: isActive ? "#ffffff" : "#cbd5e1" }}
                    className="!text-sm"
                  >
                    {p.nombre}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Cerrar sesión */}
      <div className="border-t border-slate-800 p-4">
        <button
          type="button"
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-3 !text-sm !text-slate-300 transition-colors hover:bg-red-950/50 hover:!text-red-300"
        >
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-900">
            ↪
          </span>
          <span className="font-medium">Cerrar sesión</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
