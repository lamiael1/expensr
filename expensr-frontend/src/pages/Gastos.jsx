import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { getExpenses } from "../services/api";

function esRechazoBaw(gasto) {
  const estado = (gasto.estado || "").trim().toUpperCase();

  return (
    estado === "RECHAZADO_BAW" ||
    (estado === "RECHAZADO" && !gasto.fecha_decision_appian)
  );
}

function fechaLegible(valor) {
  if (!valor) return "Pendiente";

  const fecha = new Date(valor);
  if (Number.isNaN(fecha.getTime())) return "Fecha no disponible";

  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(fecha);
}

function fechaCorta(valor) {
  if (!valor) return "—";

  const fecha = new Date(`${valor}T00:00:00`);
  if (Number.isNaN(fecha.getTime())) return valor;

  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
  }).format(fecha);
}

function moneda(valor) {
  const importe = Number(valor);

  if (!Number.isFinite(importe)) return "—";

  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
  }).format(importe);
}

function duracion(inicio, fin) {
  if (!inicio || !fin) return null;

  const minutos = Math.round(
    (new Date(fin).getTime() - new Date(inicio).getTime()) / 60000,
  );

  if (!Number.isFinite(minutos) || minutos < 0) return null;

  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;

  return horas ? `${horas} h ${resto} min` : `${minutos} min`;
}

function estadoDelGasto(gasto) {
  const estado = (gasto.estado || "").trim().toUpperCase();

  if (esRechazoBaw(gasto)) {
    return {
      clave: "rechazado",
      etiqueta: "Rechazado en BAW",
      clases: "border-red-200 bg-red-50 text-red-700",
    };
  }

  if (estado === "RECHAZADO") {
    return {
      clave: "rechazado",
      etiqueta: "Rechazado en Appian",
      clases: "border-red-200 bg-red-50 text-red-700",
    };
  }

  if (estado === "PENDIENTE_BAW") {
    return {
      clave: "pendiente_baw",
      etiqueta: "Pendiente de BAW",
      clases: "border-amber-200 bg-amber-50 text-amber-800",
    };
  }

  if (estado === "PENDIENTE_APPIAN") {
    return {
      clave: "pendiente_appian",
      etiqueta: "Pendiente de Appian",
      clases: "border-blue-200 bg-blue-50 text-blue-700",
    };
  }

  if (["APROBADO", "APROBADO_BAW"].includes(estado)) {
    return {
      clave: "aprobado",
      etiqueta: estado === "APROBADO_BAW" ? "Validado por BAW" : "Aprobado",
      clases: "border-emerald-200 bg-emerald-50 text-emerald-700",
    };
  }

  return {
    clave: "otro",
    etiqueta: estado ? estado.replaceAll("_", " ") : "Sin estado",
    clases: "border-gray-200 bg-gray-50 text-gray-700",
  };
}

function Paso({ titulo, estado, fecha, detalle }) {
  const completado = estado === "completado";
  const actual = estado === "actual";
  const rechazado = estado === "rechazado";

  let clases = "border-gray-200 bg-white";
  if (rechazado) clases = "border-red-200 bg-red-50";
  else if (completado) clases = "border-emerald-200 bg-emerald-50";
  else if (actual) clases = "border-blue-200 bg-blue-50";

  return (
    <li className={`rounded-xl border p-4 ${clases}`}>
      <p
        className={`font-semibold ${
          rechazado ? "text-red-800" : "text-gray-900"
        }`}
      >
        {titulo}
      </p>
      <p
        className={`mt-1 text-sm ${
          rechazado ? "text-red-700" : "text-gray-600"
        }`}
      >
        {detalle}
      </p>
      <p className="mt-3 text-xs text-gray-500">{fechaLegible(fecha)}</p>
    </li>
  );
}

function LineaTiempo({ gasto }) {
  const estado = (gasto.estado || "").trim().toUpperCase();
  const rechazadoBaw = esRechazoBaw(gasto);
  const bawCompletado = Boolean(gasto.fecha_validacion_baw);
  const appianCompletado = Boolean(gasto.fecha_decision_appian);

  const bawActual =
    !rechazadoBaw && !bawCompletado && estado === "PENDIENTE_BAW";
  const appianActual =
    !rechazadoBaw &&
    !appianCompletado &&
    estado === "PENDIENTE_APPIAN";

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
        estado={
          rechazadoBaw
            ? "rechazado"
            : bawCompletado
              ? "completado"
              : bawActual
                ? "actual"
                : "pendiente"
        }
        fecha={gasto.fecha_validacion_baw}
        detalle={
          rechazadoBaw
            ? `Rechazado${
                gasto.comentario_baw ? ` · ${gasto.comentario_baw}` : ""
              }`
            : bawCompletado
              ? `Validado${duracionBaw ? ` · ${duracionBaw}` : ""}`
              : bawActual
                ? "En curso"
                : "Pendiente"
        }
      />

      <Paso
        titulo="Decisión Appian"
        estado={
          rechazadoBaw
            ? "pendiente"
            : appianCompletado
              ? "completado"
              : appianActual
                ? "actual"
                : "pendiente"
        }
        fecha={gasto.fecha_decision_appian}
        detalle={
          rechazadoBaw
            ? "No aplica: el gasto fue rechazado en BAW"
            : appianCompletado
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

function Resumen({ etiqueta, valor, detalle, tono = "gray" }) {
  const tonos = {
    gray: "border-gray-200 bg-white",
    blue: "border-blue-100 bg-blue-50/70",
    red: "border-red-100 bg-red-50/70",
  };

  return (
    <article className={`rounded-2xl border p-4 shadow-sm ${tonos[tono]}`}>
      <p className="text-sm font-medium text-gray-500">{etiqueta}</p>
      <p className="mt-2 text-2xl font-bold tracking-tight text-gray-900">
        {valor}
      </p>
      <p className="mt-1 text-xs text-gray-500">{detalle}</p>
    </article>
  );
}

function Gastos() {
  const [gastos, setGastos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [actualizando, setActualizando] = useState(false);
  const [error, setError] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [estadoSeleccionado, setEstadoSeleccionado] = useState("todos");
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState("todas");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [gastoAbierto, setGastoAbierto] = useState(null);

  const cargarGastos = useCallback(async (manual = false) => {
    if (manual) setActualizando(true);

    try {
      const datos = await getExpenses();
      setGastos(Array.isArray(datos) ? datos : []);
      setError("");
    } catch {
      setError("No se pudieron cargar los gastos. Inténtalo de nuevo.");
    } finally {
      setCargando(false);
      setActualizando(false);
    }
  }, []);

  useEffect(() => {
    const temporizador = setTimeout(() => {
      void cargarGastos();
    }, 0);

    return () => clearTimeout(temporizador);
  }, [cargarGastos]);

  const categorias = useMemo(
    () =>
      [...new Set(gastos.map((gasto) => gasto.categoria).filter(Boolean))].sort(
        (a, b) => a.localeCompare(b, "es"),
      ),
    [gastos],
  );

  const gastosFiltrados = useMemo(() => {
    const texto = busqueda.trim().toLocaleLowerCase("es");

    return [...gastos]
      .filter((gasto) => {
        const estado = estadoDelGasto(gasto);
        const coincideTexto =
          !texto ||
          [
            gasto.concepto,
            gasto.categoria,
            gasto.empleado,
            gasto.estado,
            gasto.comentario_baw,
            gasto.comentario_appian,
            gasto.importe,
          ]
            .filter((valor) => valor !== null && valor !== undefined)
            .some((valor) =>
              String(valor).toLocaleLowerCase("es").includes(texto),
            );

        const coincideEstado =
          estadoSeleccionado === "todos" ||
          estado.clave === estadoSeleccionado;

        const coincideCategoria =
          categoriaSeleccionada === "todas" ||
          gasto.categoria === categoriaSeleccionada;

        const coincideDesde = !desde || gasto.fecha >= desde;
        const coincideHasta = !hasta || gasto.fecha <= hasta;

        return (
          coincideTexto &&
          coincideEstado &&
          coincideCategoria &&
          coincideDesde &&
          coincideHasta
        );
      })
      .sort((a, b) => {
        const fechaA = a.fecha_creacion || a.fecha || "";
        const fechaB = b.fecha_creacion || b.fecha || "";
        return fechaB.localeCompare(fechaA);
      });
  }, [
    gastos,
    busqueda,
    estadoSeleccionado,
    categoriaSeleccionada,
    desde,
    hasta,
  ]);

  const importeFiltrado = gastosFiltrados.reduce(
    (suma, gasto) => suma + (Number(gasto.importe) || 0),
    0,
  );

  const rechazadosFiltrados = gastosFiltrados.filter(
    (gasto) => estadoDelGasto(gasto).clave === "rechazado",
  ).length;

  function limpiarFiltros() {
    setBusqueda("");
    setEstadoSeleccionado("todos");
    setCategoriaSeleccionada("todas");
    setDesde("");
    setHasta("");
  }

  if (cargando) {
    return (
      <main className="mx-auto max-w-7xl p-6">
        <div className="animate-pulse space-y-5">
          <div className="h-8 w-48 rounded-lg bg-gray-200" />
          <div className="h-24 rounded-2xl bg-gray-100" />
          <div className="h-16 rounded-2xl bg-gray-100" />
          <div className="h-64 rounded-2xl bg-gray-100" />
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
            Expensr
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-gray-950">
            Mis gastos
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-gray-500">
            Busca tus gastos, filtra la lista y revisa en qué etapa está cada
            uno.
          </p>
        </div>

        <button
          type="button"
          onClick={() => cargarGastos(true)}
          disabled={actualizando}
          className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 shadow-sm transition hover:border-blue-200 hover:bg-blue-50 disabled:cursor-wait disabled:opacity-60"
        >
          <span aria-hidden="true">{actualizando ? "…" : "↻"}</span>
          {actualizando ? "Actualizando" : "Actualizar"}
        </button>
      </header>

      {error && (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => cargarGastos(true)}
            className="font-semibold underline underline-offset-2"
          >
            Reintentar
          </button>
        </div>
      )}

      <section
        aria-label="Resumen de gastos filtrados"
        className="grid gap-3 sm:grid-cols-3"
      >
        <Resumen
          etiqueta="Gastos encontrados"
          valor={gastosFiltrados.length}
          detalle={`de ${gastos.length} gastos registrados`}
          tono="blue"
        />
        <Resumen
          etiqueta="Importe de la selección"
          valor={moneda(importeFiltrado)}
          detalle="Suma de los gastos que cumplen los filtros"
        />
        <Resumen
          etiqueta="Rechazados"
          valor={rechazadosFiltrados}
          detalle="Dentro de los resultados actuales"
          tono={rechazadosFiltrados > 0 ? "red" : "gray"}
        />
      </section>

      <section
        aria-label="Buscar y filtrar gastos"
        className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5"
      >
        <div className="grid gap-4 lg:grid-cols-[minmax(240px,2fr)_repeat(4,minmax(140px,1fr))]">
          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
              Buscar
            </span>
            <span className="relative block">
              <span
                className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-gray-400"
                aria-hidden="true"
              >
                ⌕
              </span>
              <input
                type="search"
                value={busqueda}
                onChange={(evento) => setBusqueda(evento.target.value)}
                placeholder="Concepto, empleado, estado…"
                className="w-full rounded-xl border border-gray-200 bg-gray-50 py-2.5 pl-9 pr-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
              />
            </span>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
              Estado
            </span>
            <select
              value={estadoSeleccionado}
              onChange={(evento) => setEstadoSeleccionado(evento.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-800 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
            >
              <option value="todos">Todos los estados</option>
              <option value="pendiente_baw">Pendiente de BAW</option>
              <option value="pendiente_appian">Pendiente de Appian</option>
              <option value="aprobado">Aprobados / validados</option>
              <option value="rechazado">Rechazados</option>
              <option value="otro">Otros</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
              Categoría
            </span>
            <select
              value={categoriaSeleccionada}
              onChange={(evento) =>
                setCategoriaSeleccionada(evento.target.value)
              }
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-800 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
            >
              <option value="todas">Todas las categorías</option>
              {categorias.map((categoria) => (
                <option key={categoria} value={categoria}>
                  {categoria}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
              Desde
            </span>
            <input
              type="date"
              value={desde}
              max={hasta || undefined}
              onChange={(evento) => setDesde(evento.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-800 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
              Hasta
            </span>
            <input
              type="date"
              value={hasta}
              min={desde || undefined}
              onChange={(evento) => setHasta(evento.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-800 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
            />
          </label>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-4">
          <p className="text-sm text-gray-500" aria-live="polite">
            Mostrando{" "}
            <span className="font-semibold text-gray-800">
              {gastosFiltrados.length}
            </span>{" "}
            de {gastos.length} gastos
          </p>
          <button
            type="button"
            onClick={limpiarFiltros}
            className="rounded-lg px-3 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
          >
            Limpiar filtros
          </button>
        </div>
      </section>

      <section
        aria-label="Lista de gastos"
        className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm"
      >
        {gastosFiltrados.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <div
              className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-100 text-xl text-gray-500"
              aria-hidden="true"
            >
              ⌕
            </div>
            <h2 className="mt-4 text-lg font-semibold text-gray-900">
              No encontramos gastos
            </h2>
            <p className="mx-auto mt-1 max-w-md text-sm text-gray-500">
              Prueba con otro texto o quita alguno de los filtros aplicados.
            </p>
            <button
              type="button"
              onClick={limpiarFiltros}
              className="mt-4 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              Limpiar filtros
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left">
              <thead className="bg-gray-50/80">
                <tr className="text-xs uppercase tracking-wide text-gray-500">
                  <th className="px-5 py-3.5 font-semibold">Gasto</th>
                  <th className="px-5 py-3.5 font-semibold">Categoría</th>
                  <th className="px-5 py-3.5 font-semibold">Fecha</th>
                  <th className="px-5 py-3.5 text-right font-semibold">
                    Importe
                  </th>
                  <th className="px-5 py-3.5 font-semibold">Estado</th>
                  <th className="px-5 py-3.5 text-right font-semibold">
                    Seguimiento
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-gray-100">
                {gastosFiltrados.map((gasto) => {
                  const abierto = gastoAbierto === gasto.id;
                  const estado = estadoDelGasto(gasto);

                  return (
                    <Fragment key={gasto.id}>
                      <tr className="transition hover:bg-blue-50/40">
                        <td className="px-5 py-4">
                          <p className="font-semibold text-gray-900">
                            {gasto.concepto || "Gasto sin concepto"}
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            #{gasto.id}
                            {gasto.empleado ? ` · ${gasto.empleado}` : ""}
                          </p>
                        </td>

                        <td className="px-5 py-4 text-sm text-gray-600">
                          {gasto.categoria || "Sin categoría"}
                        </td>

                        <td className="px-5 py-4 text-sm text-gray-600">
                          {fechaCorta(gasto.fecha)}
                        </td>

                        <td className="px-5 py-4 text-right text-sm font-semibold tabular-nums text-gray-900">
                          {moneda(gasto.importe)}
                        </td>

                        <td className="px-5 py-4">
                          <span
                            className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${estado.clases}`}
                          >
                            <span
                              className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current"
                              aria-hidden="true"
                            />
                            {estado.etiqueta}
                          </span>
                        </td>

                        <td className="px-5 py-4 text-right">
                          <button
                            type="button"
                            aria-expanded={abierto}
                            aria-controls={`seguimiento-${gasto.id}`}
                            onClick={() =>
                              setGastoAbierto(abierto ? null : gasto.id)
                            }
                            className="rounded-lg px-3 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
                          >
                            {abierto ? "Ocultar" : "Ver etapas"}
                          </button>
                        </td>
                      </tr>

                      {abierto && (
                        <tr className="bg-gray-50/70">
                          <td
                            id={`seguimiento-${gasto.id}`}
                            colSpan={6}
                            className="px-5 py-5"
                          >
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
        )}
      </section>
    </main>
  );
}

export default Gastos;
