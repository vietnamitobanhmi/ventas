BEGIN;

-- Esta migración es autocontenida: incluye la monitorización por zona y
-- la conversión de kds_status de una sola fila a una fila por KDS.
ALTER TABLE public.zonas
ADD COLUMN IF NOT EXISTS monitorizar_kds boolean NOT NULL DEFAULT true;

ALTER TABLE public.zonas
ADD COLUMN IF NOT EXISTS es_kds_principal boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN public.zonas.monitorizar_kds IS
'Controla si la conexión de la tablet KDS de esta zona debe generar avisos.';

COMMENT ON COLUMN public.zonas.es_kds_principal IS
'El KDS principal ve todos los pedidos, gestiona cobros y muestra los finalizados del día.';

CREATE SEQUENCE IF NOT EXISTS public.kds_status_id_seq;

ALTER SEQUENCE public.kds_status_id_seq
OWNED BY public.kds_status.id;

INSERT INTO public.kds_status (
    id,
    zona,
    last_seen,
    last_visible,
    visibility_state,
    alerta_enviada,
    alertas_activas
)
VALUES (1, NULL, NULL, NULL, 'config', false, true)
ON CONFLICT (id) DO NOTHING;

SELECT setval(
    'public.kds_status_id_seq',
    COALESCE((SELECT MAX(id) FROM public.kds_status), 0) + 1,
    false
);

ALTER TABLE public.kds_status
ALTER COLUMN id SET DEFAULT nextval('public.kds_status_id_seq');

GRANT USAGE, SELECT ON SEQUENCE public.kds_status_id_seq
TO anon, authenticated, service_role;

CREATE UNIQUE INDEX IF NOT EXISTS kds_status_zona_uq
ON public.kds_status (zona);

-- Conserva el comportamiento actual: BARRA pasa a ser el KDS principal
-- si todavía no se ha configurado ningún principal.
UPDATE public.zonas
SET es_kds_principal = true
WHERE id = (
    SELECT id
    FROM public.zonas
    WHERE upper(trim(nombre)) = 'BARRA'
    ORDER BY id
    LIMIT 1
)
AND NOT EXISTS (
    SELECT 1
    FROM public.zonas
    WHERE es_kds_principal = true
);

-- Evita que dos zonas gestionen simultáneamente la vista global y los cobros.
CREATE UNIQUE INDEX IF NOT EXISTS zonas_un_solo_kds_principal
ON public.zonas (es_kds_principal)
WHERE es_kds_principal = true;

NOTIFY pgrst, 'reload schema';

COMMIT;
