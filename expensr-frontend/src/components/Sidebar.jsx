import { NavLink } from "react-router-dom";

function Sidebar() {
  const pestañas = [
    { ruta: "/upload", nombre: "Subir factura" },
    { ruta: "/gastos", nombre: "Mis gastos" },
    { ruta: "/chat", nombre: "Preguntar" },
    { ruta: "/monitor", nombre: "Monitoreo" },
  ];

  return (
    <aside className="w-64 min-h-screen bg-slate-900 text-white flex flex-col p-4">
      <h1 className="text-2xl font-bold mb-1">Expensr</h1>
      <p className="text-slate-400 text-sm mb-6">empleado_007</p>

      <nav className="flex flex-col gap-1">
        {pestañas.map((p) => (
          <NavLink
            key={p.ruta}
            to={p.ruta}
            className={({ isActive }) =>
              `px-3 py-2 rounded-md transition-colors ${
                isActive ? "bg-slate-700 font-semibold" : "hover:bg-slate-800"
              }`
            }
          >
            {p.nombre}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;