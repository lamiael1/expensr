INSERT INTO presupuestos (empleado, categoria, limite_mensual)
VALUES
    ('empleado_007', 'Dietas', 500.00),
    ('empleado_007', 'Transporte', 300.00),
    ('empleado_007', 'Material', 400.00),
    ('empleado_007', 'Formacion', 600.00)
ON CONFLICT (empleado, categoria) DO NOTHING;


INSERT INTO gastos (
    empleado,
    fecha,
    concepto,
    categoria,
    importe,
    adjunto_url,
    centro_coste,
    requiere_revision_manager,
    estado,
    fecha_creacion
)
VALUES
    (
        'empleado_007',
        CURRENT_DATE - INTERVAL '5 days',
        'Comida con cliente',
        'Dietas',
        85.50,
        NULL,
        'CC-100',
        FALSE,
        'PENDIENTE_BAW',
        CURRENT_TIMESTAMP - INTERVAL '5 days'
    ),
    (
        'empleado_007',
        CURRENT_DATE - INTERVAL '3 days',
        'Taxi aeropuerto',
        'Transporte',
        42.00,
        NULL,
        'CC-100',
        FALSE,
        'PENDIENTE_BAW',
        CURRENT_TIMESTAMP - INTERVAL '3 days'
    ),
    (
        'empleado_007',
        CURRENT_DATE - INTERVAL '1 day',
        'Material de oficina',
        'Material',
        120.00,
        NULL,
        'CC-100',
        FALSE,
        'PENDIENTE_BAW',
        CURRENT_TIMESTAMP - INTERVAL '1 day'
    );
