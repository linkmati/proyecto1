-- ==========================================
-- SCRIPT ENTREGABLE - FORMATO MySQL 8.x
-- ==========================================

-- Borrado de tablas
DROP TABLE IF EXISTS favoritos, mensajes, conversaciones, eventos_envio, incidencias, costes_pedidos, pedidos, ofertas, fotos_articulo, articulos, usuarios;

-- Tablas

CREATE TABLE usuarios (
    id_usuario VARCHAR(36) PRIMARY KEY, -- Simula el UUID de Supabase Auth
    email VARCHAR(255) NOT NULL UNIQUE,
    nombre_usuario VARCHAR(100),
    estado ENUM('activo', 'inactivo', 'suspendido', 'eliminado') DEFAULT 'activo' NOT NULL,
    rol VARCHAR(20) DEFAULT 'user' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE articulos (
    id_articulo BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_vendedor VARCHAR(36) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(100) NOT NULL,
    precio_base DECIMAL(10, 2) NOT NULL,
    estado_articulo ENUM('disponible', 'reservado', 'vendido', 'desactivado', 'eliminado') DEFAULT 'disponible' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_vendedor) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

CREATE TABLE fotos_articulo (
    id_foto BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_articulo BIGINT NOT NULL,
    image_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_articulo) REFERENCES articulos(id_articulo) ON DELETE CASCADE
);

CREATE TABLE ofertas (
    id_oferta BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_comprador VARCHAR(36) NOT NULL,
    id_articulo BIGINT NOT NULL,
    ultimo_emisor_id VARCHAR(36),
    estado ENUM('pendiente', 'aceptada', 'rechazada', 'caducada') DEFAULT 'pendiente' NOT NULL,
    importe DECIMAL(10, 2) NOT NULL,
    mensaje TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_comprador) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_articulo) REFERENCES articulos(id_articulo) ON DELETE CASCADE,
    FOREIGN KEY (ultimo_emisor_id) REFERENCES usuarios(id_usuario)
);

CREATE TABLE pedidos (
    id_pedido BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_comprador VARCHAR(36) NOT NULL,
    id_articulo BIGINT NOT NULL,
    estado_pedido ENUM('pendiente_pago', 'pagado', 'enviado', 'en_reparto', 'entregado', 'completado', 'cancelado') DEFAULT 'pendiente_pago' NOT NULL,
    precio_final DECIMAL(10, 2) NOT NULL,
    metodo_envio VARCHAR(100),
    desde_direccion TEXT NOT NULL,
    hacia_direccion TEXT NOT NULL,
    tracking_number VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_comprador) REFERENCES usuarios(id_usuario) ON DELETE RESTRICT,
    FOREIGN KEY (id_articulo) REFERENCES articulos(id_articulo) ON DELETE RESTRICT
);

CREATE TABLE costes_pedidos (
    id_coste BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_pedido BIGINT NOT NULL,
    tipo_coste ENUM('envio', 'comision_comprador', 'seguro_proteccion', 'extra_vendedor') NOT NULL,
    importe DECIMAL(10, 2) NOT NULL,
    moneda VARCHAR(3) DEFAULT 'EUR' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido) ON DELETE CASCADE
);

CREATE TABLE incidencias (
    id_incidencia BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_pedido BIGINT NOT NULL,
    tipo_incidencia ENUM('no_recibido', 'articulo_diferente', 'articulo_danado', 'falsificacion') NOT NULL,
    motivo TEXT NOT NULL,
    estado_incidencia ENUM('abierta', 'en_mediacion', 'resuelta_reembolso', 'resuelta_sin_reembolso', 'cerrada') DEFAULT 'abierta' NOT NULL,
    importe_reembolso DECIMAL(10, 2),
    requiere_devolucion BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido) ON DELETE CASCADE
);

CREATE TABLE eventos_envio (
    id_evento BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_pedido BIGINT NOT NULL,
    descripcion_evento TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido) ON DELETE CASCADE
);

CREATE TABLE conversaciones (
    id_conversacion BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_usuario_1 VARCHAR(36) NOT NULL,
    id_usuario_2 VARCHAR(36) NOT NULL,
    id_articulo BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario_1) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario_2) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_articulo) REFERENCES articulos(id_articulo) ON DELETE CASCADE,
    UNIQUE (id_usuario_1, id_usuario_2, id_articulo)
);

CREATE TABLE mensajes (
    id_mensaje BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_conversacion BIGINT NOT NULL,
    id_emisor VARCHAR(36) NOT NULL,
    contenido TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_conversacion) REFERENCES conversaciones(id_conversacion) ON DELETE CASCADE,
    FOREIGN KEY (id_emisor) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

CREATE TABLE favoritos (
    id_favorito BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_usuario VARCHAR(36) NOT NULL,
    id_articulo BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_articulo) REFERENCES articulos(id_articulo) ON DELETE CASCADE,
    UNIQUE (id_usuario, id_articulo)
);

-- Permisos y roles (DAC MySQL)

-- Creacion de roles
CREATE ROLE 'admin_role';
CREATE ROLE 'user_role';

-- Privilegios admin
GRANT ALL PRIVILEGES ON articulos TO 'admin_role' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON usuarios TO 'admin_role' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON ofertas TO 'admin_role' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON pedidos TO 'admin_role' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON incidencias TO 'admin_role' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON conversaciones TO 'admin_role' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON mensajes TO 'admin_role' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON favoritos TO 'admin_role' WITH GRANT OPTION;

-- Privilegios usuario normal
-- La logica a nivel de fila se hace en el backend
GRANT SELECT, INSERT, UPDATE, DELETE ON articulos TO 'user_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON ofertas TO 'user_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON conversaciones TO 'user_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON mensajes TO 'user_role';
GRANT SELECT, INSERT, DELETE ON favoritos TO 'user_role';
GRANT SELECT, INSERT ON fotos_articulo TO 'user_role';
GRANT SELECT, UPDATE ON usuarios TO 'user_role';
GRANT SELECT, INSERT, UPDATE ON pedidos TO 'user_role';

-- Usuarios de ejemplo
-- CREATE USER 'vinted_admin'@'localhost' IDENTIFIED BY 'admin123';
-- GRANT 'admin_role' TO 'vinted_admin'@'localhost';

-- CREATE USER 'vinted_user'@'localhost' IDENTIFIED BY 'user123';
-- GRANT 'user_role' TO 'vinted_user'@'localhost';

-- Revocar permisos
-- REVOKE DELETE ON articulos FROM 'user_role';
