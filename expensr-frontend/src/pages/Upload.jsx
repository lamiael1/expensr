import { useState } from "react";

function Upload() {
  const [archivo, setArchivo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setArchivo(e.target.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!archivo) return;

    setCargando(true);
    setMensaje(null);

    // Creamos el formulario multipart para enviar el archivo
    const formData = new FormData();
    formData.append("file", archivo);

    fetch("http://localhost:8000/expenses/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => {
        if (!res.ok) throw new Error("Error al subir la factura.");
        return res.json();
      })
      .then((data) => {
        setMensaje(data.message);
        setArchivo(null);
      })
      .catch((err) => setMensaje(err.message))
      .finally(() => setCargando(false));
  };

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-center">Subir factura</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Tu zona punteada actual */}
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

        {/* Botón de envío que faltaba */}
        <button
          type="submit"
          disabled={!archivo || cargando}
          className="w-full bg-slate-900 text-white py-2 px-4 rounded-md font-medium hover:bg-slate-800 disabled:bg-gray-300 transition-colors"
        >
          {cargando ? "Procesando..." : "Procesar Factura"}
        </button>
      </form>

      {/* Mensaje de confirmación tras subirse */}
      {mensaje && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-md text-sm text-center">
          {mensaje}
        </div>
      )}
    </div>
  );
}

export default Upload;
