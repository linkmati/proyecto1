# Resumen de la Base de Datos - Proyecto Vinted Clone

Este documento describe la arquitectura, funcionamiento y esquema de la base de datos utilizada en el proyecto.

## 1. Tecnología y Arquitectura

La base de datos utiliza **PostgreSQL** y está alojada en **Supabase**. Se aprovechan varias características avanzadas de Postgres:

*   **Tipos Enumerados (ENUM):** Para restringir los estados de usuarios, artículos, pedidos y ofertas a valores específicos.
*   **UUIDs:** Sincronizados con el sistema de autenticación de Supabase (`auth.users`) para una gestión de sesiones segura.
*   **Row Level Security (RLS):** Las políticas de seguridad están implementadas directamente en la base de datos, garantizando que los usuarios solo puedan acceder o modificar los datos que les corresponden.
*   **Integridad Referencial:** Uso extensivo de claves foráneas con reglas `ON DELETE CASCADE` o `RESTRICT` para mantener la consistencia de los datos.

## 2. Entidades Principales

La base de datos se organiza en torno a las siguientes tablas:

| Tabla | Descripción |
| :--- | :--- |
| **usuarios** | Almacena el perfil básico, rol (user/admin) y estado de los usuarios. |
| **articulos** | Productos publicados para la venta, incluyendo descripción, categoría y precio. |
| **fotos_articulo** | Galería de imágenes asociadas a cada artículo. |
| **ofertas** | Registro de negociaciones de precio entre compradores y vendedores. |
| **pedidos** | Transacciones finalizadas, incluyendo direcciones de envío y estado del paquete. |
| **costes_pedidos** | Desglose de costes adicionales (envío, comisión, seguro) de un pedido. |
| **incidencias** | Gestión de reclamaciones y disputas sobre pedidos. |
| **eventos_envio** | Historial de estados por los que pasa el paquete de un pedido. |
| **conversaciones** | Agrupador de chats entre dos usuarios sobre un artículo específico. |
| **mensajes** | Contenido individual de los chats dentro de una conversación. |
| **favoritos** | Relación de artículos marcados como favoritos por los usuarios. |

## 3. Funcionamiento de los Estados (Enums)

El flujo del sistema se controla mediante diversos enums:

*   **estado_articulo:** `disponible`, `reservado`, `vendido`, `desactivado`, `eliminado`.
*   **estado_pedido:** `pendiente_pago`, `pagado`, `enviado`, `en_reparto`, `entregado`, `completado`, `cancelado`.
*   **estado_oferta:** `pendiente`, `aceptada`, `rechazada`, `caducada`.
*   **estado_incidencia:** `abierta`, `en_mediacion`, `resuelta_reembolso`, `resuelta_sin_reembolso`, `cerrada`.

## 4. Diagrama Entidad-Relación (ERD)

A continuación se presenta el diagrama completo de las relaciones entre las tablas:

```mermaid
erDiagram
    usuarios ||--o{ articulos : "vende"
    usuarios ||--o{ ofertas : "compra/oferta"
    usuarios ||--o{ pedidos : "compra"
    usuarios ||--o{ favoritos : "marca"
    usuarios ||--o{ conversaciones : "participa_1"
    usuarios ||--o{ conversaciones : "participa_2"
    usuarios ||--o{ mensajes : "envía"

    articulos ||--o{ fotos_articulo : "tiene"
    articulos ||--o{ ofertas : "recibe"
    articulos ||--o{ pedidos : "se_convierte_en"
    articulos ||--o{ favoritos : "es_marcado"
    articulos ||--o{ conversaciones : "origina"

    pedidos ||--o{ costes_pedidos : "tiene_desglose"
    pedidos ||--o{ incidencias : "puede_tener"
    pedidos ||--o{ eventos_envio : "tiene_seguimiento"

    conversaciones ||--o{ mensajes : "contiene"

    usuarios {
        uuid id_usuario PK
        string email
        string nombre_usuario
        enum estado
        string rol
        timestamp created_at
    }

    articulos {
        bigint id_articulo PK
        uuid id_vendedor FK
        string titulo
        text descripcion
        string categoria
        numeric precio_base
        enum estado_articulo
        timestamp created_at
    }

    fotos_articulo {
        bigint id_foto PK
        bigint id_articulo FK
        text image_url
    }

    ofertas {
        bigint id_oferta PK
        uuid id_comprador FK
        bigint id_articulo FK
        uuid ultimo_emisor_id FK
        enum estado
        numeric importe
        text mensaje
    }

    pedidos {
        bigint id_pedido PK
        uuid id_comprador FK
        bigint id_articulo FK
        enum estado_pedido
        numeric precio_final
        string metodo_envio
        text desde_direccion
        text hacia_direccion
        string tracking_number
    }

    costes_pedidos {
        bigint id_coste PK
        bigint id_pedido FK
        enum tipo_coste
        numeric importe
        string moneda
    }

    incidencias {
        bigint id_incidencia PK
        bigint id_pedido FK
        enum tipo_incidencia
        text motivo
        enum estado_incidencia
        numeric importe_reembolso
        boolean requiere_devolucion
    }

    conversaciones {
        bigint id_conversacion PK
        uuid id_usuario_1 FK
        uuid id_usuario_2 FK
        bigint id_articulo FK
    }

    mensajes {
        bigint id_mensaje PK
        bigint id_conversacion FK
        uuid id_emisor FK
        text contenido
        boolean leido
    }

    favoritos {
        bigint id_favorito PK
        uuid id_usuario FK
        bigint id_articulo FK
    }
```
