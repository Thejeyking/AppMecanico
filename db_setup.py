import sqlite3

# Define el nombre de tu archivo de base de datos
DB_NAME = 'taller_mecanico.db'

def crear_tablas():
    conn = None
    try:
        # Conectar a la base de datos (o crearla si no existe)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # --- Tabla clientes ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                telefono TEXT,
                email TEXT,
                dni TEXT UNIQUE
            )
        ''')

        # --- Tabla vehiculos ---
        # Un cliente puede tener muchos vehículos, por eso se enlaza con cliente_id
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                anio INTEGER,
                patente TEXT UNIQUE NOT NULL,
                kilometraje_inicial INTEGER,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        ''')

        # --- Tabla mecanicos ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mecanicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                dni TEXT UNIQUE
            )
        ''')

        # --- Tabla turnos ---
        # Un turno tiene un vehículo asociado y un mecánico asignado
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                mecanico_id INTEGER,
                fecha_hora DATETIME NOT NULL,
                estimacion_reparacion TEXT,
                estado TEXT DEFAULT 'Pendiente', -- Ej: 'Pendiente', 'En Taller', 'Finalizado', 'Cancelado'
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
            )
        ''')

        # --- Tabla reparaciones (detalles de cada vez que un auto entró al taller para ser reparado) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reparaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                mecanico_id INTEGER,
                fecha_ingreso DATETIME NOT NULL,
                fecha_salida DATETIME,
                kilometraje_ingreso INTEGER NOT NULL,
                problema_reportado TEXT,
                trabajo_realizado TEXT,
                costo_mano_obra REAL DEFAULT 0.0,
                costo_total REAL DEFAULT 0.0,
                estado TEXT DEFAULT 'En Progreso', -- Ej: 'En Progreso', 'Finalizada', 'Pendiente de Pago'
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
            )
        ''')

        # --- Tabla repuestos_usados (para cada repuesto específico dentro de una reparación) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repuestos_usados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reparacion_id INTEGER NOT NULL,
                nombre_repuesto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                costo_unitario REAL NOT NULL,
                costo_total_repuesto REAL AS (cantidad * costo_unitario) STORED, -- Calcula automáticamente el costo
                FOREIGN KEY (reparacion_id) REFERENCES reparaciones(id)
            )
        ''')

        # Confirmar los cambios y guardar en la base de datos
        conn.commit()
        print(f"Tablas creadas en {DB_NAME} exitosamente.")

    except sqlite3.Error as e:
        print(f"Error al crear tablas: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    crear_tablas()