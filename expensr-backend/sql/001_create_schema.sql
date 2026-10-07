CREATE TABLE IF NOT EXISTS gastos (
    id BIGSERIAL PRIMARY KEY,
    empleado VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    importe NUMERIC(10, 2) NOT NULL CHECK (importe >= 0),
    adjunto_url TEXT,

    centro_coste VARCHAR(100),
    requiere_revision_manager BOOLEAN NOT NULL DEFAULT FALSE,
    estado VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE_BAW',
    comentario_baw TEXT,
    fecha_validacion_baw TIMESTAMPTZ,

    acumulado_mes NUMERIC(10, 2),
    presupuesto_restante NUMERIC(10, 2),
    decision_final VARCHAR(50),
    comentario_appian TEXT,
    fecha_decision_appian TIMESTAMPTZ,

    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS presupuestos (
    id BIGSERIAL PRIMARY KEY,
    empleado VARCHAR(100) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    limite_mensual NUMERIC(10, 2) NOT NULL CHECK (limite_mensual >= 0),

    CONSTRAINT uq_presupuesto_empleado_categoria
        UNIQUE (empleado, categoria)
);

CREATE INDEX IF NOT EXISTS idx_gastos_empleado
    ON gastos (empleado);

CREATE INDEX IF NOT EXISTS idx_gastos_estado
    ON gastos (estado);

CREATE INDEX IF NOT EXISTS idx_gastos_fecha_creacion
    ON gastos (fecha_creacion);
