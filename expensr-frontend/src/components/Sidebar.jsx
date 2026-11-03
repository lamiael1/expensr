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
    sessionStorage.removeItem("expensr_chat_messages");
    localStorage.removeItem("expensr_user");
    navigate("/login", { replace: true });
  };

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-slate-800 bg-slate-950 text-white md:sticky md:top-0 md:h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="border-b border-slate-800 px-4 py-3 sm:px-5 md:py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white shadow-sm md:h-11 md:w-11">
            <span className="text-xl font-black text-slate-950">E</span>
          </div>

          <div className="min-w-0">
            <h1 className="!m-0 !text-2xl !font-extrabold !tracking-tight !text-white md:!text-3xl">
              Expensr
            </h1>
            <p className="!mt-1 !text-xs !font-medium !text-slate-300">
              Gestión de gastos
            </p>
          </div>
        </div>
      </div>

      <div className="px-3 py-2 md:px-4 md:py-5">
        <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 md:py-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-700 font-semibold !text-white md:h-10 md:w-10">
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

      <nav
        aria-label="Navegación principal"
        className="min-w-0 flex-1 px-2 pb-2 md:px-3 md:py-5"
      >
        <p className="mb-3 hidden px-3 !text-[11px] !font-bold uppercase !tracking-widest !text-slate-500 md:block">
          Navegación
        </p>

        <div className="-mx-2 flex gap-1 overflow-x-auto px-2 pb-1 md:mx-0 md:flex-col md:space-y-1 md:overflow-visible md:px-0 md:pb-0">
          {pestañas.map((p) => (
            <NavLink
              key={p.ruta}
              to={p.ruta}
              style={({ isActive }) => ({
                color: isActive ? "#ffffff" : "#cbd5e1",
                backgroundColor: isActive ? "#4f46e5" : "transparent",
              })}
              className={({ isActive }) =>
                `flex shrink-0 items-center gap-2 rounded-lg px-3 py-2.5 !no-underline transition-colors duration-150 md:w-full md:gap-3 md:rounded-xl md:py-3 ${
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
                    className="whitespace-nowrap !text-sm"
                  >
                    {p.nombre}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="border-t border-slate-800 p-2 md:p-4">
        <button
          type="button"
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 !text-sm !text-slate-300 transition-colors hover:bg-red-950/50 hover:!text-red-300 md:py-3"
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
