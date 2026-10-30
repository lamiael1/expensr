import { Fragment, useEffect, useState } from "react";
import { getExpenses } from "../services/api";

function fechaLegible(valor) {
  if (!valor) return "Pendiente";

  const fecha = new Date(valor);
  if (Number.isNaN(fecha.getTime())) return "Fecha no disponible";

  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(fecha);
}

function duracion(inicio, fin) {
  if (!inicio || !fin) return null;

  const minutos = Math.round((new Date(fin) - new Date(inicio)) / 60000);
  if (!Number.isFinite(minutos) || minutos < 0) return null;

  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;

  return horas ? `${horas} h ${resto} min` : `${minutos} min`;
}

function Paso({ titulo, estado, fecha, detalle }) {
  const completado = estado === "completado";
  const actual = estado === "actual";

  return (
    <li
      className={`rounded-lg border p-4 ${
        completado
          ? "border-emerald-200 bg-emerald-50"
          : actual
            ? "border-indigo-300 bg-indigo-50"
            : "border-gray-200 bg-white"
      }`}
    >
      <p className="font-semibold text-gray-900">{titulo}</p>
      <p className="mt-1 text-sm text-gray-600">{detalle}</p>
      <p className="mt-2 text-xs text-gray-500">{fechaLegible(fecha)}</p>
    </li>
  );
}

function LineaTiempo({ gasto }) {
  const bawCompletado = Boolean(gasto.fecha_validacion_baw);
  const appianCompletado = Boolean(gasto.fecha_decision_appian);

  const bawActual =
    !bawCompletado && gasto.estado === "PENDIENTE_BAW";
  const appianActual =
    !appianCompletado && gasto.estado === "PENDIENTE_APPIAN";

  const duracionBaw = duracion(
    gasto.fecha_creacion,
    gasto.fecha_validacion_baw,
  );

  const duracionAppian = duracion(
    gasto.fecha_validacion_baw || gasto.fecha_creacion,
    gasto.fecha_decision_appian,
  );

  return (
    <ol className="grid gap-3 md:grid-cols-3" aria-label="Seguimiento del gasto">
      <Paso
        titulo="Gasto registrado"
        estado="completado"
        fecha={gasto.fecha_creacion}
        detalle="Guardado en Expensr"
      />

      <Paso
        titulo="Validación BAW"
        estado={bawCompletado ? "completado" : bawActual ? "actual" : "pendiente"}
        fecha={gasto.fecha_validacion_baw}
        detalle={
          bawCompletado
            ? `Validado${duracionBaw ? ` · ${duracionBaw}` : ""}`
            : bawActual
              ? "En curso"
              : "Pendiente"
        }
      />

      <Paso
        titulo="Decisión Appian"
        estado={
          appianCompletado ? "completado" : appianActual ? "actual" : "pendiente"
        }
        fecha={gasto.fecha_decision_appian}
        detalle={
          appianCompletado
            ? `${gasto.decision_final || "Decisión registrada"}${
                duracionAppian ? ` · ${duracionAppian}` : ""
              }`
            : appianActual
              ? "Pendiente de decisión financiera"
              : "A la espera de la validación BAW"
        }
      />
    </ol>
  );
}

function Gastos() {
  const [gastos, setGastos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [gastoAbierto, setGastoAbierto] = useState(null);

  useEffect(() => {
    getExpenses()
      .then(setGastos)
      .catch(() => setError("No se pudieron cargar los gastos."))
      .finally(() => setCargando(false));
  }, []);

  if (cargando) return <p>Cargando...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  return (
    <main>
      <h2 className="mb-4 text-xl font-semibold">Mis gastos</h2>

      <div className="overflow-x-auto rounded-lg bg-white shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-gray-600">
              <th className="p-3">Fecha</th>
              <th className="p-3">Categoría</th>
              <th className="p-3">Importe</th>
              <th className="p-3">Seguimiento</th>
            </tr>
          </thead>

          <tbody>
            {gastos.map((gasto) => {
              const abierto = gastoAbierto === gasto.id;

              return (
                <Fragment key={gasto.id}>
                  <tr className="border-t">
                    <td className="p-3">{gasto.fecha}</td>
                    <td className="p-3">{gasto.categoria}</td>
                    <td className="p-3">{gasto.importe} €</td>
                    <td className="p-3">
                      <button
                        type="button"
                        aria-expanded={abierto}
                        onClick={() =>
                          setGastoAbierto(abierto ? null : gasto.id)
                        }
                        className="font-medium text-indigo-700 hover:text-indigo-900"
                      >
                        {abierto ? "Ocultar" : "Ver etapas"}
                      </button>
                    </td>
                  </tr>

                  {abierto && (
                    <tr className="border-t bg-gray-50">
                      <td colSpan={4} className="p-4">
                        <LineaTiempo gasto={gasto} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </main>
  );
}

export default Gastos;
