import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getMonitorOverview } from "../services/api";

const REFRESH_MS = 30000;

function formatHoras(horas) {
  if (horas === null || horas === undefined) return "—";
  if (horas < 1) return `${Math.round(horas * 60)} min`;
  if (horas < 24) return `${horas.toFixed(1)} h`;

  const dias = Math.floor(horas / 24);
  const resto = Math.round(horas - dias * 24);
  return `${dias} d ${resto} h`;
}

function formatDia(dia) {
  const [, mes, numero] = dia.split("-");
  return `${numero}/${mes}`;
}

function KpiCard({ label, value, detail, color }) {
  return (
    <article
      className={`rounded-xl border border-gray-200 border-l-4 ${color} bg-white p-5 shadow-sm`}
    >
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-3 text-3xl font-bold text-gray-900">{value}</p>
      {detail && <p className="mt-1 text-xs text-gray-500">{detail}</p>}
    </article>
  );
}

function Monitor() {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdate, setLastUpdate] = useState(null);
  const [now, setNow] = useState(() => Date.now());

  const loadOverview = useCallback(async () => {
    try {
      setError("");
      const data = await getMonitorOverview();
      setOverview(data);
      setLastUpdate(Date.now());
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
    const interval = setInterval(loadOverview, REFRESH_MS);

    return () => {
      clearTimeout(timeout);
      clearInterval(interval);
    };
  }, [loadOverview]);

  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(tick);
  }, []);

  const segundos = lastUpdate
    ? Math.max(0, Math.floor((now - lastUpdate) / 1000))
    : null;

  const serie = (overview?.series_tiempos ?? []).map((punto) => ({
    dia: formatDia(punto.dia),
    BAW: punto.baw_horas,
    Appian: punto.appian_horas,
  }));

  const instancias = (overview?.instancias ?? []).slice(0, 5);

  return (
    <main className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Monitoreo de procesos
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Estado de los gastos en BAW y Appian, obtenido a través del backend.
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

      {loading && !overview && (
        <p className="text-sm text-gray-500" role="status">
          Cargando métricas...
        </p>
      )}

      {overview && (
        <>
          <section
            aria-label="Indicadores"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
          >
            <KpiCard
              label="Procesos en curso"
              value={overview.en_curso}
              detail={`${overview.pending_baw} en BAW · ${overview.pending_appian} en Appian`}
              color="border-blue-500"
            />
            <KpiCard
              label="Completados hoy"
              value={overview.completados_hoy}
              detail={`${overview.approved} aprobados · ${overview.rejected} rechazados`}
              color="border-emerald-500"
            />
            <KpiCard
              label="Tiempo medio"
              value={formatHoras(overview.tiempo_medio_horas)}
              detail="Desde la creación hasta la decisión"
              color="border-amber-500"
            />
            <KpiCard
              label="SLA cumplido"
              value={
                overview.sla_pct === null || overview.sla_pct === undefined
                  ? "—"
                  : `${overview.sla_pct} %`
              }
              detail="Resueltos en 48 h o menos"
              color="border-violet-500"
            />
          </section>

          <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">
                Tiempo medio por etapa (últimos 7 días)
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Horas medias en BAW y en Appian, por día de creación del gasto.
              </p>

              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={serie}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="dia" />
                    <YAxis unit=" h" />
                    <Tooltip formatter={(valor) => `${valor} h`} />
                    <Legend />
                    <Bar dataKey="BAW" stackId="tiempo" fill="#60a5fa" />
                    <Bar dataKey="Appian" stackId="tiempo" fill="#1e3a8a" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">
                Instancias recientes
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Los 5 gastos más recientes y su etapa actual.
              </p>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500">
                      <th className="py-2 pr-3 font-medium">Instancia</th>
                      <th className="py-2 pr-3 font-medium">Sistema</th>
                      <th className="py-2 pr-3 font-medium">Etapa</th>
                      <th className="py-2 font-medium">Duración</th>
                    </tr>
                  </thead>
                  <tbody>
                    {instancias.map((instancia) => (
                      <tr key={instancia.id} className="border-t">
                        <td className="py-2 pr-3 font-semibold text-gray-900">
                          #{instancia.id}
                        </td>
                        <td className="py-2 pr-3 text-gray-700">
                          {instancia.sistema}
                        </td>
                        <td className="py-2 pr-3 text-gray-700">
                          {instancia.etapa_actual}
                        </td>
                        <td className="py-2 text-gray-700">
                          {formatHoras(instancia.horas_en_etapa)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {instancias.length === 0 && (
                  <p className="py-4 text-sm text-gray-500">
                    Todavía no hay gastos registrados.
                  </p>
                )}
              </div>
            </div>
          </section>
        </>
      )}

      <p className="flex items-center gap-2 text-xs text-gray-500">
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            error ? "bg-red-500" : "bg-emerald-500"
          }`}
        />
        {segundos === null
          ? "Sin datos todavía."
          : `Última actualización: hace ${segundos}s · se actualiza cada 30 s.`}
      </p>
    </main>
  );
}

export default Monitor;
