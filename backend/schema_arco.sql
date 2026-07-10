-- ============================================================
-- TABLE: arco_requests
-- Tabla para solicitudes ARCO (Ley 21.719)
-- ============================================================

CREATE TABLE IF NOT EXISTS `aif369-backend.aif369_analytics.arco_requests` (
  arco_id STRING NOT NULL,  -- Identificador único de la solicitud
  timestamp TIMESTAMP NOT NULL,  -- Cuándo se recibió la solicitud
  tipo_derecho STRING NOT NULL,  -- acceso, rectificacion, cancelacion, oposicion
  nombre STRING,  -- Nombre completo del solicitante
  run STRING,  -- Número de identificación (RUN en Chile)
  email STRING NOT NULL,  -- Email de contacto
  detalle STRING,  -- Detalles adicionales de la solicitud
  estado STRING DEFAULT "pendiente",  -- pendiente, procesado, completado, denegado
  respuesta_timestamp TIMESTAMP,  -- Cuándo se completó
  ip_address STRING,  -- IP del solicitante
  user_agent STRING,  -- Navegador/cliente
  origin STRING,  -- Origen de la solicitud
  notas_internas STRING,  -- Notas para el DPO
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY tipo_derecho, estado, email
WITH CONNECTION OPTIONS (
  description="Solicitudes de derechos ARCO según Ley 21.719 Chile"
);

-- ============================================================
-- VIEW: arco_statistics
-- Para reportes de cumplimiento de ARCO
-- ============================================================

CREATE OR REPLACE VIEW `aif369-backend.aif369_analytics.arco_statistics` AS
SELECT
  DATE(created_at) as fecha,
  tipo_derecho,
  estado,
  COUNT(*) as total_solicitudes,
  COUNT(DISTINCT email) as solicitantes_unicos,
  AVG(DATE_DIFF(CURRENT_DATE(), DATE(created_at), DAY)) as dias_promedio_resolucion
FROM
  `aif369-backend.aif369_analytics.arco_requests`
GROUP BY
  fecha, tipo_derecho, estado
ORDER BY
  fecha DESC;

-- ============================================================
-- VIEW: arco_compliance
-- Para auditoría de cumplimiento (15 días máximo)
-- ============================================================

CREATE OR REPLACE VIEW `aif369-backend.aif369_analytics.arco_compliance` AS
SELECT
  arco_id,
  email,
  tipo_derecho,
  created_at,
  respuesta_timestamp,
  estado,
  DATE_DIFF(DATE(respuesta_timestamp), DATE(created_at), DAY) as dias_para_resolver,
  CASE
    WHEN estado = "completado" AND DATE_DIFF(DATE(respuesta_timestamp), DATE(created_at), DAY) <= 15 THEN "CUMPLIDO"
    WHEN estado = "completado" AND DATE_DIFF(DATE(respuesta_timestamp), DATE(created_at), DAY) > 15 THEN "FUERA_PLAZO"
    WHEN estado = "pendiente" AND DATE_DIFF(CURRENT_DATE(), DATE(created_at), DAY) > 15 THEN "INCUMPLIDO"
    ELSE "CONFORME"
  END as estado_cumplimiento
FROM
  `aif369-backend.aif369_analytics.arco_requests`
WHERE
  created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
ORDER BY
  created_at DESC;
