import { useState } from "react";

function Upload() {
  const [archivo, setArchivo] = useState(null);

  function manejarDrop(e) {
    e.preventDefault();
    setArchivo(e.dataTransfer.files[0]);
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Subir factura</h2>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={manejarDrop}
        className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center"
      >
        {archivo ? archivo.name : "Arrastra la factura aquí"}
      </div>
    </div>
  );
}

export default Upload;