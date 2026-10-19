import { useState } from "react";
import { extractInvoice, createExpense } from "../services/api";

const CATEGORIAS = ["Dietas", "Transporte", "Material", "Formacion"];

function Upload() {
  const [archivo, setArchivo] = useState(null);
  const [extrayendo, setExtrayendo] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);
  const [exito, setExito] = useState(null);
  const [datos, setDatos] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setArchivo(file);
    setDatos(null);
    setError(null);
    setExito(null);
  };

  const handleExtraer = async () => {
    if (!archivo) return;

    setExtrayendo(true);
    setError(null);

    try {
      const extraido = await extractInvoice(archivo);
      setDatos({
        fecha: extraido.fecha ?? new Date().toISOString().slice(0, 10),
        importe: extraido.importe ?? "",
        categoria: extraido.categoria ?? CATEGORIAS[0],
        concepto: extraido.concepto ?? "",
      });
    } catch (err) {
      setError(err.message || "No se pudieron extraer los datos de la factura.");
    } finally {
      setExtrayendo(false);
    }
  };

  const handleCampoChange = (campo, valor) => {
    setDatos((prev) => ({ ...prev, [campo]: valor }));
  };

  const handleConfirmar = async (e) => {
    e.preventDefault();
    if (!datos) return;

    const storedUser = JSON.parse(localStorage.getItem("expensr_user") || "{}");

    setEnviando(true);
    setError(null);

    try {
      await createExpense({
        empleado: storedUser.empleado || "empleado_007",
        fecha: datos.fecha,
        concepto: datos.concepto,
        categoria: datos.categoria,
        importe: parseFloat(datos.importe),
        adjunto_url: archivo?.name ?? null,
      });

      setExito("Gasto enviado a validación correctamente.");
      setArchivo(null);
      setDatos(null);
    } catch (err) {
      setError(err.message || "No se pudo enviar el gasto.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-center">Subir factura</h2>

      <div className="border-2 border-dashed border-gray-300 p-12 rounded-lg text-center bg-white shadow-sm relative">
        <input
          type="file"
          accept="image/*,.pdf"
          onChange={handleFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        {archivo ? (
          <p className="text-gray-700 font-medium">{archivo.name}</p>
        ) : (
          <p className="text-gray-400">Arrastra tu factura aquí o haz clic para seleccionar</p>
        )}
      </div>

      {archivo && !datos && (
        <button
          type="button"
          onClick={handleExtraer}
          disabled={extrayendo}
          className="w-full bg-slate-900 text-white py-2 px-4 rounded-md font-medium hover:bg-slate-800 disabled:bg-gray-300 transition-colors"
        >
          {extrayendo ? "Extrayendo datos con IA..." : "Procesar factura"}
        </button>
      )}

      {datos && (
        <form onSubmit={handleConfirmar} className="space-y-4 bg-white p-6 rounded-lg shadow-sm">
          <p className="text-sm text-gray-500">
            Datos extraídos automáticamente. Revisa y corrige si hace falta.
          </p>

          <div>
            <label className="block text-sm font-medium mb-1">Fecha</label>
            <input
              type="date"
              value={datos.fecha}
              onChange={(e) => handleCampoChange("fecha", e.target.value)}
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Importe (€)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={datos.importe}
              onChange={(e) => handleCampoChange("importe", e.target.value)}
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Categoría</label>
            <select
              value={datos.categoria}
              onChange={(e) => handleCampoChange("categoria", e.target.value)}
              className="w-full border rounded-md px-3 py-2"
            >
              {CATEGORIAS.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Concepto</label>
            <input
              type="text"
              value={datos.concepto}
              onChange={(e) => handleCampoChange("concepto", e.target.value)}
              className="w-full border rounded-md px-3 py-2"
              required
            />
          </div>

          <button
            type="submit"
            disabled={enviando}
            className="w-full bg-emerald-600 text-white py-2 px-4 rounded-md font-medium hover:bg-emerald-700 disabled:bg-gray-300 transition-colors"
          >
            {enviando ? "Enviando..." : "Enviar a validación"}
          </button>
        </form>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm text-center">
          {error}
        </div>
      )}

      {exito && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-md text-sm text-center">
          {exito}
        </div>
      )}
    </div>
  );
}

export default Upload;
