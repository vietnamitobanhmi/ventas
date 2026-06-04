-- ═══════════════════════════════════════════════════
-- PASO 1: Borrar policies existentes si las hay
-- ═══════════════════════════════════════════════════
DROP POLICY IF EXISTS "config_public_read" ON config;
DROP POLICY IF EXISTS "categorias_public_read" ON categorias;
DROP POLICY IF EXISTS "productos_public_read" ON productos;
DROP POLICY IF EXISTS "pedidos_public_insert" ON pedidos;
DROP POLICY IF EXISTS "pedido_items_public_insert" ON pedido_items;
DROP POLICY IF EXISTS "reservas_public_insert" ON reservas;

-- ═══════════════════════════════════════════════════
-- PASO 2: Activar RLS en todas las tablas
-- ═══════════════════════════════════════════════════
ALTER TABLE config ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedido_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE reservas ENABLE ROW LEVEL SECURITY;
ALTER TABLE ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE empleados ENABLE ROW LEVEL SECURITY;
ALTER TABLE turnos ENABLE ROW LEVEL SECURITY;
ALTER TABLE procesos ENABLE ROW LEVEL SECURITY;
ALTER TABLE pasos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ejecuciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE ejecucion_pasos ENABLE ROW LEVEL SECURITY;

-- ═══════════════════════════════════════════════════
-- PASO 3: Policies para la web pública (anon key)
-- Solo lectura en config, categorias, productos
-- Solo inserción en pedidos, pedido_items, reservas
-- ═══════════════════════════════════════════════════
CREATE POLICY "config_public_read" ON config
    FOR SELECT TO anon USING (true);

CREATE POLICY "categorias_public_read" ON categorias
    FOR SELECT TO anon USING (true);

CREATE POLICY "productos_public_read" ON productos
    FOR SELECT TO anon USING (true);

CREATE POLICY "pedidos_public_insert" ON pedidos
    FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "pedido_items_public_insert" ON pedido_items
    FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "reservas_public_insert" ON reservas
    FOR INSERT TO anon WITH CHECK (true);

-- ═══════════════════════════════════════════════════
-- El resto de tablas (ventas, empleados, turnos, etc.)
-- NO tienen policies para anon = sin acceso público
-- El backoffice usa service_role que bypasea RLS
-- ═══════════════════════════════════════════════════
