import { NavLink, useNavigate } from "react-router-dom";

function Sidebar() {
  const navigate = useNavigate();

  const pestañas = [
    { ruta: "/upload", nombre: "Subir factura", icono: "↑" },
    { ruta: "/gastos", nombre: "Mis gastos", icono: "€" },
    { ruta: "/chat", nombre: "Preguntar", icono: "?" },
    { ruta: "/monitor", nombre: "Monitoreo", icono: "◉" },
  ];

  const user = JSON.parse(localStorage.getItem("expensr_user") || "{}");

  const handleLogout = () => {
    localStorage.removeItem("expensr_user");
    navigate("/login", { replace: true });
  };

  return (
    <aside className="w-64 min-h-screen bg-slate-950 text-white flex flex-col border-r border-slate-800">
      {/* Logo */}
      <div className="px-5 pt-6 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-white flex items-center justify-center shadow-sm">
            <span className="text-slate-950 font-black text-xl">E</span>
          </div>

          <div>
            <h1 className="!text-white text-3xl font-extrabold tracking-tight">
              Expensr
            </h1>

            <p className="!text-slate-300 text-xs mt-1 font-medium">
              Gestión de gastos
            </p>
          </div>
        </div>
      </div>

      {/* Usuario */}
      <div className="px-4 py-5">
        <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-slate-900 border border-slate-800">
          <div className="w-10 h-10 shrink-0 rounded-full bg-slate-700 flex items-center justify-center text-white font-semibold">
            {(user.nombre || "E").charAt(0).toUpperCase()}
          </div>

          <div className="min-w-0">
            <p className="text-white text-sm font-semibold truncate">
              {user.nombre || "Empleado"}
            </p>
            <p className="text-slate-400 text-xs truncate mt-0.5">
              {user.empleado || "empleado_007"}
            </p>
          </div>
        </div>
      </div>

      {/* Menú */}
      <nav className="flex-1 px-3">
        <p className="px-3 mb-3 text-[11px] font-bold uppercase tracking-widest text-slate-500">
          Navegación
        </p>

        <div className="space-y-1">
          {pestañas.map((p) => (
            <NavLink
              key={p.ruta}
              to={p.ruta}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-3 rounded-xl text-sm transition-all ${
                  isActive
                    ? "bg-white text-slate-950 font-semibold shadow-md"
                    : "text-slate-300 hover:bg-slate-900 hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold ${
                      isActive
                        ? "bg-slate-100 text-slate-950"
                        : "bg-slate-900 text-slate-400"
                    }`}
                  >
                    {p.icono}
                  </span>

                  <span>{p.nombre}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Cerrar sesión */}
      <div className="p-4 border-t border-slate-800">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-slate-300 hover:bg-red-950/50 hover:text-red-300 transition-colors"
        >
          <span className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center">
            ↪
          </span>

          <span className="font-medium">Cerrar sesión</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
