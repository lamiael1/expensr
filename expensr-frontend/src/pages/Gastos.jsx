import { useState, useEffect } from "react";

function Gastos() {
  const [gastos, setGastos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/expenses")
      .then((res) => res.json())
      .then(setGastos)
      .catch(() => setError("No se pudieron cargar los gastos."))
      .finally(() => setCargando(false));
  }, []);

  if (cargando) return <p>Cargando...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Mis gastos</h2>
      <table className="w-full bg-white rounded-lg shadow-sm">
        <thead>
          <tr className="text-left text-sm text-gray-600">
            <th className="p-3">Fecha</th>
            <th className="p-3">Categoría</th>
            <th className="p-3">Importe</th>
          </tr>
        </thead>
        <tbody>
          {gastos.map((g) => (
            <tr key={g.id} className="border-t">
              <td className="p-3">{g.fecha}</td>
              <td className="p-3">{g.categoria}</td>
              <td className="p-3">{g.importe} €</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Gastos;