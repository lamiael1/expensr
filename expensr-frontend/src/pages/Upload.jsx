import { useRef, useState } from "react";
import { extractInvoice, createExpense } from "../services/api";

const CATEGORIAS = ["Dietas", "Transporte", "Material", "Formacion"];

function Upload() {
  const inputRef = useRef(null);

  const [archivo, setArchivo] = useState(null);
  const [extrayendo, setExtrayendo] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [arrastrando, setArrastrando] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState("");
  const [datos, setDatos] = useState(null);

  const seleccionarArchivo = (file) => {
    if (!file) return;

    const esPDF =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");
    const esImagen = file.type.startsWith("image/");

    if (!esPDF && !esImagen) {
      setError("Selecciona un archivo PDF o una imagen.");
      setExito("");
      return;
    }

    setArchivo(file);
    setDatos(null);
    setError("");
    setExito("");
  };

  const handleFileChange = (e) => {
    seleccionarArchivo(e.target.files?.[0]);
    e.target.value = "";
  };

  const handleExtraer = async () => {
    if (!archivo || extrayendo || enviando) return;

    setExtrayendo(true);
    setError("");
    setExito("");

    try {
      const extraido = await extractInvoice(archivo);

      setDatos({
        fecha: extraido.fecha ?? new Date().toISOString().slice(0, 10),
        importe: extraido.importe ?? "",
        categoria: CATEGORIAS.includes(extraido.categoria)
          ? extraido.categoria
          : CATEGORIAS[0],
        concepto: extraido.concepto ?? "",
      });
    } catch (err) {
      setError(
        err.message || "No se pudieron extraer los datos de la factura.",
      );
    } finally {
      setExtrayendo(false);
    }
  };

  const handleCampoChange = (campo, valor) => {
    setDatos((prev) => ({ ...prev, [campo]: valor }));
  };

  const handleConfirmar = async (e) => {
    e.preventDefault();

    if (!datos || enviando || extrayendo) return;

    const importe = Number(datos.importe);

    if (!Number.isFinite(importe) || importe <= 0) {
      setError("Introduce un importe válido mayor que cero.");
      return;
    }

    if (!datos.fecha || !datos.concepto.trim()) {
      setError("Completa la fecha y el concepto antes de registrar el gasto.");
      return;
    }

    const storedUser = (() => {
      try {
        return JSON.parse(localStorage.getItem("expensr_user") || "{}");
      } catch {
        return {};
      }
    })();

    setEnviando(true);
    setError("");
    setExito("");

    try {
      const nuevoGasto = await createExpense({
        empleado: storedUser.empleado || "empleado_007",
        fecha: datos.fecha,
        concepto: datos.concepto.trim(),
        categoria: datos.categoria,
        importe,
        adjunto_url: archivo?.name ?? null,
      });

      if (nuevoGasto.baw_instance_id) {
        setExito(
          `Gasto registrado e inicio confirmado en BAW. Instancia creada: #${nuevoGasto.baw_instance_id}`
        );
      } else {
        setExito(
          "Gasto registrado en Expensr como PENDIENTE_BAW (sin confirmación de instancia en BAW)."
        );
      }

      setArchivo(null);
      setDatos(null);

      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (err) {
      setError(err.message || "No se pudo registrar el gasto.");
    } finally {
      setEnviando(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setArrastrando(false);
    seleccionarArchivo(e.dataTransfer.files?.[0]);
  };

  const limpiarArchivo = () => {
    setArchivo(null);
    setDatos(null);
    setError("");
    setExito("");

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  return (
    <section className="mx-auto w-full max-w-5xl space-y-8">
      <header className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">
          Gestión de gastos
        </p>

        <h2 className="!m-0 !text-3xl !font-bold !tracking-tight !text-slate-900">
          Subir factura
        </h2>

        <p className="max-w-2xl text-sm leading-6 text-slate-500">
          Sube el justificante de tu gasto. Extraeremos los datos
          automáticamente para que puedas revisarlos antes de registrar el gasto
          en Expensr.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {[
          { numero: "01", titulo: "Sube la factura", detalle: "PDF o imagen" },
          {
            numero: "02",
            titulo: "Revisa los datos",
            detalle: "Extracción automática",
          },
          {
            numero: "03",
            titulo: "Registra el gasto",
            detalle: "Quedará pendiente de validación BAW",
          },
        ].map((paso, indice) => {
          const completado =
            (indice === 0 && Boolean(archivo)) ||
            (indice === 1 && Boolean(datos)) ||
            (indice === 2 && Boolean(exito));

          return (
            <div
              key={paso.numero}
              className={`flex items-start gap-3 rounded-xl border p-4 ${
                completado
                  ? "border-indigo-200 bg-indigo-50"
                  : "border-slate-200 bg-white"
              }`}
            >
              <span
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-bold ${
                  completado
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-100 text-slate-500"
                }`}
              >
                {paso.numero}
              </span>

              <div>
                <p className="text-sm font-semibold text-slate-800">
                  {paso.titulo}
                </p>
                <p className="mt-1 text-xs text-slate-500">{paso.detalle}</p>
              </div>
            </div>
          );
        })}
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="mb-5">
          <h3 className="!m-0 !text-lg !font-semibold !text-slate-900">
            1. Selecciona tu justificante
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            Puedes arrastrar el archivo a la zona inferior o seleccionarlo desde
            tu dispositivo.
          </p>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setArrastrando(true);
          }}
          onDragLeave={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) {
              setArrastrando(false);
            }
          }}
          onDrop={handleDrop}
          className={`relative rounded-xl border-2 border-dashed p-7 text-center transition-colors sm:p-10 ${
            arrastrando
              ? "border-indigo-500 bg-indigo-50"
              : "border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50/50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,image/*,.pdf"
            onChange={handleFileChange}
            aria-label="Seleccionar archivo de factura"
            className="sr-only"
          />

          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-2xl text-indigo-700">
            ↑
          </div>

          {archivo ? (
            <>
              <p className="mt-4 break-all font-semibold text-slate-800">
                {archivo.name}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {(archivo.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-3">
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100"
                >
                  Cambiar archivo
                </button>

                <button
                  type="button"
                  onClick={limpiarArchivo}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-red-600 transition-colors hover:bg-red-50"
                >
                  Quitar archivo
                </button>
              </div>
            </>
          ) : (
            <>
              <p className="mt-4 font-semibold text-slate-800">
                Arrastra tu factura aquí
              </p>
              <p className="mt-1 text-sm text-slate-500">
                o selecciona un archivo desde tu equipo
              </p>

              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="mt-5 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-indigo-600"
              >
                Seleccionar archivo
              </button>

              <p className="mt-4 text-xs text-slate-400">
                Formatos admitidos: PDF e imágenes
              </p>
            </>
          )}
        </div>

        {archivo && !datos && (
          <button
            type="button"
            onClick={handleExtraer}
            disabled={extrayendo || enviando}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {extrayendo ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                Extrayendo datos con IA...
              </>
            ) : (
              "Procesar factura"
            )}
          </button>
        )}
      </section>

      {datos && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
          <div className="mb-6">
            <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">
              Paso 2
            </p>
            <h3 className="mt-2 !text-xl !font-bold !text-slate-900">
              Revisa los datos extraídos
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              La extracción automática puede contener errores. Comprueba los
              campos antes de registrar el gasto.
            </p>
          </div>

          <form onSubmit={handleConfirmar} className="space-y-5">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="fecha-gasto"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Fecha del gasto
                </label>
                <input
                  id="fecha-gasto"
                  type="date"
                  value={datos.fecha}
                  onChange={(e) => handleCampoChange("fecha", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="importe-gasto"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Importe (€)
                </label>
                <div className="relative">
                  <input
                    id="importe-gasto"
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={datos.importe}
                    onChange={(e) =>
                      handleCampoChange("importe", e.target.value)
                    }
                    placeholder="0,00"
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 pr-10 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                    required
                  />
                  <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-sm text-slate-400">
                    €
                  </span>
                </div>
              </div>

              <div>
                <label
                  htmlFor="categoria-gasto"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Categoría
                </label>
                <select
                  id="categoria-gasto"
                  value={datos.categoria}
                  onChange={(e) =>
                    handleCampoChange("categoria", e.target.value)
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  required
                >
                  {CATEGORIAS.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="concepto-gasto"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Concepto
                </label>
                <input
                  id="concepto-gasto"
                  type="text"
                  value={datos.concepto}
                  onChange={(e) =>
                    handleCampoChange("concepto", e.target.value)
                  }
                  placeholder="Ej. Desplazamiento a cliente"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  required
                />
              </div>
            </div>

            <div className="flex flex-col gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:justify-between">
              <button
                type="button"
                onClick={() => {
                  setDatos(null);
                  setError("");
                }}
                disabled={enviando}
                className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50"
              >
                Volver al archivo
              </button>

              <button
                type="submit"
                disabled={enviando || extrayendo}
                className="rounded-lg bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {enviando ? "Registrando gasto..." : "Registrar gasto"}
              </button>
            </div>
          </form>
        </section>
      )}

      {error && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
        >
          <span className="font-bold" aria-hidden="true">
            !
          </span>
          <p>{error}</p>
        </div>
      )}

      {exito && (
        <div
          role="status"
          className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800"
        >
          <span className="font-bold" aria-hidden="true">
            ✓
          </span>
          <p>{exito}</p>
        </div>
      )}
    </section>
  );
}

export default Upload;
