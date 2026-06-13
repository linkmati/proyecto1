# Estándares y Normas de Bases de Datos

Este documento resume las convenciones, reglas y estándares técnicos extraídos de los materiales de la asignatura (Temas 2-7).

## 1. Diseño y Modelado Conceptual (Tema 2)
*   **Notación:** **Chen** (obligatorio).
    *   Entidades: Rectángulos.
    *   Relaciones: Rombos.
    *   Atributos: Óvalos.
*   **Paso al Modelo Relacional (Tablas):**
    *   **1:N:** Propagar clave del lado 1 al lado N como FK.
    *   **N:M:** Crear tabla intermedia con PK compuesta (ambas FKs).
    *   **1:1:** FK en la tabla con participación total (o según lógica de negocio).
    *   **Atributos Multievaluados:** Se convierten en una tabla independiente.

## 2. Normalización (Tema 3)
Objetivo: Eliminar redundancia y anomalías.
*   **1FN:** Atributos atómicos, sin grupos repetitivos.
*   **2FN:** Estar en 1FN + Dependencia funcional completa (no dependencias de parte de la PK).
*   **3FN:** Estar en 2FN + Sin dependencias transitivas (no dependencias entre atributos no clave).
*   **FNBC:** Estar en 3FN + Cada determinante debe ser clave candidata.
*   **4FN:** Estar en FNBC + Sin dependencias multievaluadas.

## 3. SQL - Lenguaje de Definición de Datos (Tema 5)
*   **Entorno:** MySQL 8.x.
*   **Restricciones (Constraints):**
    *   `PRIMARY KEY`: Clave primaria.
    *   `FOREIGN KEY`: Clave ajena + `REFERENCES`.
    *   `NOT NULL`: Campo obligatorio.
    *   `CHECK (condicion)`: Validaciones (MySQL 8.0.16+).
    *   `UNIQUE`: Unicidad.
    *   `DEFAULT`: Valor predeterminado.
*   **Integridad:** Definir comportamiento en `ON DELETE` / `ON UPDATE` (`CASCADE`, `RESTRICT`, `SET NULL`).

## 4. SQL - Lenguaje de Manipulación de Datos (Tema 4)
*   **DML:** `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
*   **Cláusulas:** `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`.
*   **Joins:** Preferir sintaxis estándar (`INNER JOIN`, `LEFT JOIN`).

## 5. Seguridad y Transacciones (Tema 6)
*   **Usuarios y Roles:**
    *   `CREATE USER 'user'@'host' IDENTIFIED BY 'pass';`
    *   `CREATE ROLE 'role_name';`
*   **Privilegios (DAC):**
    *   `GRANT <privs> ON <obj> TO <sujeto> [WITH GRANT OPTION];`
    *   `REVOKE <privs> ON <obj> FROM <sujeto> [CASCADE|RESTRICT];`
*   **Transacciones (ACID):**
    *   `START TRANSACTION;`
    *   `COMMIT;` / `ROLLBACK;`

## 6. SQL Empotrado en Python (Tema 7)
*   **Librería:** `mysql-connector-python`.
*   **Patrón de Ejecución:**
    ```python
    import mysql.connector
    conn = mysql.connector.connect(...)
    cursor = conn.cursor()
    
    # Consultas seguras (Parametrizadas)
    query = "SELECT * FROM tabla WHERE id = %s"
    cursor.execute(query, (id_val,))
    
    # Mutaciones (Requieren commit)
    conn.commit()
    
    cursor.close()
    conn.close()
    ```
