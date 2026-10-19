
import { useCallback, useEffect, useState } from "react";
import { getMonitorOverview } from "../services/api";

const initialOverview = {
  total_expenses: 0,
  total_amount: 0,
  pending_baw: 0,
  pending_appian: 0,
  approved: 0,
  rejected: 0,
};

const metrics = [
  {
    key: "total_expenses",
    label: "Gastos registrados",
    color: "border-blue-500",
  },
  {
    key: "pending_baw",
    label: "Pendientes de BAW",
    color: "border-amber-500",
  },
  {
    key: "pending_appian",
    label: "Pendientes de Appian",
    color: "border-violet-500",
  },
  {
    key: "approved",
    label: "Gastos aprobados",
    color: "border-emerald-500",
  },
  {
    key: "rejected",
    label: "Gastos rechazados",
    color: "border-red-500",
  },
];

function Monitor() {
  const [overview, setOverview] = useState(initialOverview);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadOverview = useCallback(async () => {
    try {
      setError("");
      const data = await getMonitorOverview();
      setOverview({ ...initialOverview, ...data });
    } catch {
      setError(
        "No se han podido actualizar las métricas. Comprueba que la API y PostgreSQL estén disponibles.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeout = setTimeout(loadOverview, 0);
    const interval = setInterval(loadOverview, 30000);

    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
    };
  }, [loadOverview]);

  const formatAmount = (amount) =>
    new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
    }).format(amount);

  return (
    <main className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Monitor de Expensr
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Seguimiento de los gastos registrados en el sistema.
          </p>
        </div>

        <button
          type="button"
          onClick={loadOverview}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-wait disabled:opacity-60"
        >
          {loading ? "Actualizando..." : "Actualizar"}
        </button>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {loading && (
        <p className="text-sm text-gray-500" role="status">
          Cargando métricas...
        </p>
      )}

      <section
        aria-label="Resumen de gastos"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
      >
        {metrics.map((metric) => (
          <article
            key={metric.key}
            className={`rounded-xl border border-gray-200 border-l-4 ${metric.color} bg-white p-5 shadow-sm`}
          >
            <p className="text-sm font-medium text-gray-500">
              {metric.label}
            </p>
            <p className="mt-3 text-3xl font-bold text-gray-900">
              {overview[metric.key]}
            </p>
          </article>
        ))}

        <article className="rounded-xl border border-gray-200 border-l-4 border-cyan-500 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-gray-500">
            Importe total registrado
          </p>
          <p className="mt-3 text-3xl font-bold text-gray-900">
            {formatAmount(overview.total_amount)}
          </p>
        </article>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">
          Estado de los gastos
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Distribución actual según los estados devueltos por la API.
        </p>

        <div className="mt-5 space-y-4">
          {[
            {
              label: "Pendientes de BAW",
              value: overview.pending_baw,
              color: "bg-amber-500",
            },
            {
              label: "Pendientes de Appian",
              value: overview.pending_appian,
              color: "bg-violet-500",
            },
            {
              label: "Aprobados",
              value: overview.approved,
              color: "bg-emerald-500",
            },
            {
              label: "Rechazados",
              value: overview.rejected,
              color: "bg-red-500",
            },
          ].map((item) => {
            const percentage =
              overview.total_expenses > 0
                ? Math.min(
                    100,
                    (item.value / overview.total_expenses) * 100,
                  )
                : 0;

            return (
              <div key={item.label}>
                <div className="mb-1 flex justify-between gap-3 text-sm">
                  <span className="text-gray-700">{item.label}</span>
                  <span className="font-semibold text-gray-900">
                    {item.value}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                  <div
                    className={`h-full rounded-full ${item.color}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <p className="text-xs text-gray-500">
        Actualización automática cada 30 segundos. Las métricas reflejan los
        datos disponibles en el backend; la integración con los motores de
        procesos BAW y Appian está pendiente.
      </p>
    </main>
  );
}

export default Monitor;
