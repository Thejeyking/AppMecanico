import sqlite3
import bcrypt # Necesario para hashear contraseñas
import os # Nuevo: para leer variables de entorno

# NUEVO: Importar psycopg2 para PostgreSQL
# Asegúrate de haberlo instalado con 'pip install psycopg2-binary'
import psycopg2
from psycopg2 import Error as Psycopg2Error

# --- Configuración de la Base de Datos ---
# DATABASE_URL será establecida por el servicio de hosting (ej. Render) en producción.
# Si no está definida, la aplicación usará SQLite para desarrollo local.
DATABASE_URL = os.environ.get('DATABASE_URL') 
DATABASE_FILE = 'taller_mecanico.db'

def obtener_conexion():
    """
    Establece y devuelve una conexión a la base de datos.
    Detecta automáticamente si debe conectar a PostgreSQL (si DATABASE_URL existe)
    o a SQLite (para desarrollo local).
    """
    conn = None
    if DATABASE_URL:
        # Modo PostgreSQL (para despliegue en la nube)
        try:
            conn = psycopg2.connect(DATABASE_URL)
            # Psycopg2 no necesita row_factory como SQLite3; los resultados se obtienen diferente.
            # Los resultados se mapearán a diccionarios usando _map_row_to_dict.
            print("DEBUG DB: Conectado a PostgreSQL.")
        except Psycopg2Error as e:
            print(f"Error al conectar a PostgreSQL: {e}")
            conn = None # Asegúrate de que conn sea None si falla la conexión
    else:
        # Modo SQLite (para desarrollo local)
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre (ej. fila['nombre'])
            print("DEBUG DB: Conectado a SQLite.")
        except sqlite3.Error as e:
            print(f"Error al conectar a SQLite: {e}")
            conn = None
    return conn

def crear_tablas(): # Nombre de función: crear_tablas (ESPAÑOL)
    """
    Crea las tablas necesarias en la base de datos si no existen.
    Adapta la sintaxis SQL para PostgreSQL o SQLite según la conexión activa.
    """
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Determinar si la conexión es a PostgreSQL para adaptar la sintaxis SQL
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            # Definiciones de tablas con sintaxis adaptada
            # Para AUTOINCREMENT en PostgreSQL se usa SERIAL o IDENTITY BY DEFAULT AS IDENTITY
            # Usaremos SERIAL para PostgreSQL, que es más comúnmente soportado en esta versión.

            # Tabla Clientes
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS clientes (
                    id {'SERIAL' if is_postgresql else 'INTEGER'} PRIMARY KEY{' AUTOINCREMENT' if not is_postgresql else ''},
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    dni TEXT UNIQUE
                )
            ''')

            # Tabla Usuarios_Clientes (para login de clientes)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS usuarios_clientes (
                    id {'SERIAL' if is_postgresql else 'INTEGER'} PRIMARY KEY{' AUTOINCREMENT' if not is_postgresql else ''},
                    cliente_id INTEGER UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Mecanicos (Solo datos personales del mecánico, sin credenciales de login aquí)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS mecanicos (
                    id {'SERIAL' if is_postgresql else 'INTEGER'} PRIMARY KEY{' AUTOINCREMENT' if not is_postgresql else ''},
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT
                )
            ''')

            # Tabla Usuarios_Mecanicos (Credenciales de login para mecánicos)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS usuarios_mecanicos (
                    id {'SERIAL' if is_postgresql else 'INTEGER'} PRIMARY KEY{' AUTOINCREMENT' if not is_postgresql else ''},
                    mecanico_id INTEGER UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Vehiculos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS vehiculos (
                    id {'SERIAL' if is_postgresql else 'INTEGER'} PRIMARY KEY{' AUTOINCREMENT' if not is_postgresql else ''},
                    cliente_id INTEGER NOT NULL,
                    patente TEXT UNIQUE NOT NULL,
                    marca TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    anio INTEGER,
                    kilometraje_inicial INTEGER,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Turnos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS turnos (
                    id {'SERIAL' if is_postgresql else 'INTEGER'} PRIMARY KEY{' AUTOINCREMENT' if not is_postgresql else ''},
                    cliente_id INTEGER NOT NULL,
                    vehiculo_id INTEGER NOT NULL,
                    mecanico_id INTEGER,
                    fecha TEXT NOT NULL,             -- Almacena la fecha (YYYY-MM-DD)
                    hora TEXT NOT NULL,              -- Almacena la hora (HH:MM)
                    problema_reportado TEXT NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'Agendado', -- Ej: Agendado, Completado, Cancelado, En Progreso
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
                    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE SET NULL
                )
            ''')

            # Tabla Reparaciones
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS reparaciones (
                    id {'SERIAL' if is_postgresql else 'INTEGER'} PRIMARY KEY{' AUTOINCREMENT' if not is_postgresql else ''},
                    vehiculo_id INTEGER NOT NULL,
                    mecanico_id INTEGER,
                    fecha_ingreso TEXT NOT NULL,
                    fecha_salida TEXT,
                    kilometraje_ingreso INTEGER NOT NULL,
                    kilometraje_salida INTEGER,
                    problema_reportado TEXT,
                    trabajos_realizados TEXT,
                    repuestos_usados TEXT,
                    costo_mano_obra REAL,
                    costo_total REAL,
                    estado TEXT NOT NULL DEFAULT 'En Progreso', -- Ej: Pendiente, En Progreso, Completado, Cancelado, En Espera de Repuestos
                    turno_origen_id INTEGER UNIQUE,
                    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE SET NULL,
                    FOREIGN KEY (turno_origen_id) REFERENCES turnos(id) ON DELETE SET NULL
                )
            ''')
            
            conn.commit()
            print("Base de datos inicializada o verificada correctamente.")
        except (sqlite3.Error, Psycopg2Error) as e: # Captura errores de SQLite y Psycopg2
            print(f"Error al crear tablas: {e}")
        finally:
            if conn:
                conn.close()

# --- Función auxiliar para mapear filas a diccionarios (para Psycopg2) ---
def _map_row_to_dict(cursor, row):
    """
    Mapea una tupla de resultados de Psycopg2 a un diccionario.
    Similar a sqlite3.Row para compatibilidad con el código existente.
    """
    if not row:
        return None
    
    # Obtener los nombres de las columnas del cursor
    columns = [desc[0] for desc in cursor.description]
    return {col: row[i] for i, col in enumerate(columns)}


# --- Funciones de Gestión de Clientes ---
# **NOTA:** Las consultas SQL usan '%s' como marcador de posición para PostgreSQL
# y el retorno de ID usa 'RETURNING id' para PostgreSQL.
# Se mantienen las comprobaciones de error para SQLite e IntegrityError.
def agregar_cliente(nombre, apellido, telefono, email, dni):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clientes (nombre, apellido, telefono, email, dni)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''', (nombre, apellido, telefono, email, dni))
            cliente_id = cursor.fetchone()[0] # Obtener el ID para PostgreSQL (o SQLite con RETURNING)
            conn.commit()
            return cliente_id
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            print(f"Error al agregar cliente: {e}")
            conn.rollback() # Rollback en caso de error para PostgreSQL
            return False
        finally:
            if conn: conn.close()
    return False

def obtener_todos_los_clientes():
    conn = obtener_conexion()
    clientes = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nombre, apellido, telefono, email, dni FROM clientes ORDER BY apellido, nombre')
            raw_clientes = cursor.fetchall()
            if isinstance(conn, psycopg2.extensions.connection): # Adaptar para Psycopg2
                clientes = [_map_row_to_dict(cursor, row) for row in raw_clientes]
            else: # SQLite
                clientes = [dict(row) for row in raw_clientes]
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener todos los clientes: {e}")
        finally:
            if conn: conn.close()
    return clientes

def obtener_cliente_por_id(cliente_id):
    conn = obtener_conexion()
    cliente = None
    if conn:
        try:
            cursor = conn.cursor()
            # Marcador de posición %s para psycopg2
            cursor.execute('SELECT id, nombre, apellido, telefono, email, dni FROM clientes WHERE id = %s', (cliente_id,))
            raw_cliente = cursor.fetchone()
            if raw_cliente:
                if isinstance(conn, psycopg2.extensions.connection):
                    cliente = _map_row_to_dict(cursor, raw_cliente)
                else:
                    cliente = dict(raw_cliente)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener cliente por ID: {e}")
        finally:
            if conn: conn.close()
    return cliente

def obtener_cliente_por_username(username):
    conn = obtener_conexion()
    cliente_data = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.nombre, c.apellido, c.telefono, c.email, c.dni, uc.username, uc.id AS usuario_cliente_id
                FROM clientes c
                JOIN usuarios_clientes uc ON c.id = uc.cliente_id
                WHERE uc.username = %s
            ''', (username,))
            raw_cliente = cursor.fetchone()
            if raw_cliente:
                if isinstance(conn, psycopg2.extensions.connection):
                    cliente_data = _map_row_to_dict(cursor, raw_cliente)
                else:
                    cliente_data = dict(raw_cliente)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener cliente por username: {e}")
        finally:
            if conn: conn.close()
    return cliente_data


def actualizar_cliente(cliente_id, nombre, apellido, telefono, email, dni):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE clientes
                SET nombre = %s, apellido = %s, telefono = %s, email = %s, dni = %s
                WHERE id = %s
            ''', (nombre, apellido, telefono, email, dni, cliente_id))
            conn.commit()
            return True
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            print(f"Error al actualizar cliente: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def eliminar_cliente(cliente_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM clientes WHERE id = %s', (cliente_id,))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al eliminar cliente: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

# Funciones de cliente_app (registro y login de clientes)
def obtener_cliente_por_nombre_apellido(nombre, apellido):
    conn = obtener_conexion()
    cliente = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nombre, apellido, telefono, email, dni FROM clientes WHERE nombre = %s AND apellido = %s', (nombre, apellido))
            raw_cliente = cursor.fetchone()
            if raw_cliente:
                if isinstance(conn, psycopg2.extensions.connection):
                    cliente = _map_row_to_dict(cursor, raw_cliente)
                else:
                    cliente = dict(raw_cliente)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener cliente por nombre y apellido: {e}")
        finally:
            if conn: conn.close()
    return cliente

def registrar_cliente_con_usuario(nombre, apellido, username, password, telefono=None, email=None, dni=None):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Verificar si el username ya existe
            cursor.execute('SELECT id FROM usuarios_clientes WHERE username = %s', (username,))
            if cursor.fetchone():
                return False, "El nombre de usuario ya existe."
            
            # 2. Intentar agregar el cliente.
            try:
                cursor.execute('''
                    INSERT INTO clientes (nombre, apellido, telefono, email, dni)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (nombre, apellido, telefono, email, dni))
                cliente_id = cursor.fetchone()[0] # Obtener ID para PostgreSQL
            except (sqlite3.IntegrityError, Psycopg2Error) as e:
                # Detección de error de unicidad más robusta para PostgreSQL y SQLite
                if "unique constraint" in str(e).lower() and "dni" in str(e).lower():
                    conn.rollback()
                    return False, f"El DNI '{dni}' ya está registrado."
                else:
                    print(f"Error de integridad al insertar cliente: {e}")
                    conn.rollback()
                    return False, f"Error de base de datos al registrar cliente: {e}"

            # 3. Hashear la contraseña
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # 4. Insertar el usuario asociado al cliente
            cursor.execute('''
                INSERT INTO usuarios_clientes (cliente_id, username, password)
                VALUES (%s, %s, %s)
            ''', (cliente_id, username, hashed_password))
            
            conn.commit()
            return True, "Cliente y usuario registrados con éxito."
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error en registrar_cliente_con_usuario: {e}")
            conn.rollback()
            return False, f"Error al registrar: {e}"
        finally:
            if conn: conn.close()
    return False, "Error de conexión a la base de datos."


def verificar_credenciales_cliente(username, password):
    conn = obtener_conexion()
    cliente_data = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT uc.password, c.id AS cliente_id, uc.id AS usuario_cliente_id, uc.username FROM usuarios_clientes uc JOIN clientes c ON uc.cliente_id = c.id WHERE uc.username = %s', (username,))
            user_record_raw = cursor.fetchone()

            if user_record_raw:
                # Usa la función auxiliar para mapear la fila a diccionario
                user_record = _map_row_to_dict(cursor, user_record_raw) if isinstance(conn, psycopg2.extensions.connection) else dict(user_record_raw)
                
                stored_hashed_password = user_record['password'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
                    cliente_data = user_record
                    del cliente_data['password'] # No devolver el hash de la contraseña
            
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al verificar credenciales de cliente: {e}")
        finally:
            if conn: conn.close()
    return cliente_data

def reasignar_cliente_a_usuario_cliente(usuario_cliente_id, nuevo_cliente_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios_clientes
                SET cliente_id = %s
                WHERE id = %s
            ''', (nuevo_cliente_id, usuario_cliente_id))
            conn.commit()
            print(f"DEBUG DB: Usuario cliente {usuario_cliente_id} reasignado al cliente {nuevo_cliente_id}.")
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al reasignar cliente a usuario_cliente: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False


# --- Funciones de Gestión de Mecánicos ---
def agregar_mecanico(nombre, apellido, telefono, email, username, password):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Paso 1: Insertar el mecánico
            cursor.execute('''
                INSERT INTO mecanicos (nombre, apellido, telefono, email)
                VALUES (%s, %s, %s, %s) RETURNING id
            ''', (nombre, apellido, telefono, email))
            mecanico_id = cursor.fetchone()[0] # Obtener ID para PostgreSQL

            # Paso 2: Hashear la contraseña
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Paso 3: Insertar las credenciales
            cursor.execute('''
                INSERT INTO usuarios_mecanicos (mecanico_id, username, password)
                VALUES (%s, %s, %s)
            ''', (mecanico_id, username, hashed_password))
            
            conn.commit()
            return True
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            print(f"Error al agregar mecánico y usuario: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def obtener_todos_los_mecanicos():
    conn = obtener_conexion()
    mecanicos = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nombre, apellido, telefono, email FROM mecanicos ORDER BY apellido, nombre')
            raw_mecanicos = cursor.fetchall()
            if isinstance(conn, psycopg2.extensions.connection):
                mecanicos = [_map_row_to_dict(cursor, row) for row in raw_mecanicos]
            else:
                mecanicos = [dict(row) for row in raw_mecanicos]
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener todos los mecánicos: {e}")
        finally:
            if conn: conn.close()
    return mecanicos

def obtener_mecanico_por_id(mecanico_id):
    conn = obtener_conexion()
    mecanico = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nombre, apellido, telefono, email FROM mecanicos WHERE id = %s', (mecanico_id,))
            raw_mecanico = cursor.fetchone()
            if raw_mecanico:
                if isinstance(conn, psycopg2.extensions.connection):
                    mecanico = _map_row_to_dict(cursor, raw_mecanico)
                else:
                    mecanico = dict(raw_mecanico)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener mecánico por ID: {e}")
        finally:
            if conn: conn.close()
    return mecanico

def actualizar_mecanico(mecanico_id, nombre, apellido, telefono, email):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE mecanicos
                SET nombre = %s, apellido = %s, telefono = %s, email = %s
                WHERE id = %s
            ''', (nombre, apellido, telefono, email, mecanico_id))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al actualizar mecánico: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def eliminar_mecanico(mecanico_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM mecanicos WHERE id = %s', (mecanico_id,))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al eliminar mecánico: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def verificar_credenciales_mecanico(username, password):
    conn = obtener_conexion()
    mecanico_data = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT um.password, m.* FROM usuarios_mecanicos um JOIN mecanicos m ON um.mecanico_id = m.id WHERE um.username = %s', (username,))
            user_record_raw = cursor.fetchone()

            if user_record_raw:
                user_record = _map_row_to_dict(cursor, user_record_raw) if isinstance(conn, psycopg2.extensions.connection) else dict(user_record_raw)
                
                stored_hashed_password = user_record['password'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
                    mecanico_data = user_record
                    del mecanico_data['password'] 
            
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al verificar credenciales de mecánico: {e}")
        finally:
            if conn: conn.close()
    return mecanico_data


# --- Funciones de Gestión de Vehículos ---
def agregar_vehiculo(cliente_id, patente, marca, modelo, anio, kilometraje_inicial):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO vehiculos (cliente_id, patente, marca, modelo, anio, kilometraje_inicial)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            ''', (cliente_id, patente, marca, modelo, anio, kilometraje_inicial))
            conn.commit()
            return True
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            print(f"Error al agregar vehículo: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def obtener_vehiculos_por_cliente(cliente_id):
    conn = obtener_conexion()
    vehiculos = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT v.id, v.cliente_id, v.patente, v.marca, v.modelo, v.anio, v.kilometraje_inicial,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente
                FROM vehiculos v
                JOIN clientes c ON v.cliente_id = c.id
                WHERE v.cliente_id = %s
                ORDER BY v.patente
            ''', (cliente_id,))
            raw_vehiculos = cursor.fetchall()
            if isinstance(conn, psycopg2.extensions.connection):
                vehiculos = [_map_row_to_dict(cursor, row) for row in raw_vehiculos]
            else:
                vehiculos = [dict(row) for row in raw_vehiculos]
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener vehículos por cliente {cliente_id}: {e}")
        finally:
            if conn: conn.close()
    return vehiculos

def obtener_vehiculo_por_id(vehiculo_id):
    conn = obtener_conexion()
    vehiculo = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT v.id, v.cliente_id, v.patente, v.marca, v.modelo, v.anio, v.kilometraje_inicial,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente
                FROM vehiculos v
                JOIN clientes c ON v.cliente_id = c.id
                WHERE v.id = %s
            ''', (vehiculo_id,))
            raw_vehiculo = cursor.fetchone()
            if raw_vehiculo:
                if isinstance(conn, psycopg2.extensions.connection):
                    vehiculo = _map_row_to_dict(cursor, raw_vehiculo)
                else:
                    vehiculo = dict(raw_vehiculo)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener vehículo por ID {vehiculo_id}: {e}")
        finally:
            if conn: conn.close()
    return vehiculo

def actualizar_vehiculo(vehiculo_id, marca, modelo, anio, patente, kilometraje_inicial):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE vehiculos
                SET marca = %s, modelo = %s, anio = %s, patente = %s, kilometraje_inicial = %s
                WHERE id = %s
            ''', (marca, modelo, anio, patente, kilometraje_inicial, vehiculo_id))
            conn.commit()
            return True
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            print(f"Error al actualizar vehículo: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def eliminar_vehiculo(vehiculo_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM vehiculos WHERE id = %s', (vehiculo_id,))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al eliminar vehículo: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False


# --- Funciones de Gestión de Turnos ---
def agregar_turno(cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO turnos (cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, 'Agendado'))
            conn.commit()
            print(f"Turno agendado con éxito para cliente {cliente_id}, vehículo {vehiculo_id}.")
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al agregar turno: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def obtener_todos_los_turnos():
    conn = obtener_conexion()
    turnos = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.fecha, t.hora, t.problema_reportado, t.estado,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente,
                       v.patente, v.marca, v.modelo,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico
                FROM turnos t
                JOIN clientes c ON t.cliente_id = c.id
                JOIN vehiculos v ON t.vehiculo_id = v.id
                LEFT JOIN mecanicos m ON t.mecanico_id = m.id
                WHERE t.estado IN ('Agendado', 'En Progreso', 'Cancelado')
                ORDER BY t.fecha DESC, t.hora DESC
            ''')
            raw_turnos = cursor.fetchall()
            if isinstance(conn, psycopg2.extensions.connection):
                turnos = [_map_row_to_dict(cursor, row) for row in raw_turnos]
            else:
                turnos = [dict(row) for row in raw_turnos]
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener todos los turnos: {e}")
        finally:
            if conn: conn.close()
    return turnos

def obtener_turno_por_id(turno_id):
    conn = obtener_conexion()
    turno = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.cliente_id, t.vehiculo_id, t.mecanico_id, t.fecha, t.hora, t.problema_reportado, t.estado,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente, c.dni, c.telefono, c.email,
                       v.patente, v.marca AS marca_vehiculo, v.modelo AS modelo_vehiculo, v.anio AS anio_vehiculo,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico
                FROM turnos t
                JOIN clientes c ON t.cliente_id = c.id
                JOIN vehiculos v ON t.vehiculo_id = v.id
                LEFT JOIN mecanicos m ON t.mecanico_id = m.id
                WHERE t.id = %s
            ''', (turno_id,))
            raw_turno = cursor.fetchone()
            if raw_turno:
                if isinstance(conn, psycopg2.extensions.connection):
                    turno = _map_row_to_dict(cursor, raw_turno)
                else:
                    turno = dict(raw_turno)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener turno por ID {turno_id}: {e}")
        finally:
            if conn: conn.close()
    return turno

def actualizar_turno(turno_id, cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, estado):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE turnos
                SET cliente_id = %s, vehiculo_id = %s, mecanico_id = %s, fecha = %s, hora = %s, problema_reportado = %s, estado = %s
                WHERE id = %s
            ''', (cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, estado, turno_id))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al actualizar turno: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def eliminar_turno(turno_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM turnos WHERE id = %s', (turno_id,))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al eliminar turno: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

# --- Funciones de Gestión de Reparaciones ---

def agregar_reparacion(vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, turno_origen_id=None):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reparaciones (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, estado, turno_origen_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, 'En Progreso', turno_origen_id))
            reparacion_id = cursor.fetchone()[0] # Obtener ID para PostgreSQL
            conn.commit()
            return reparacion_id
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            if "unique constraint" in str(e).lower() and "turno_origen_id" in str(e).lower():
                print(f"Advertencia: Ya existe una reparación para el turno de origen {turno_origen_id}.")
            else:
                print(f"Error de integridad al agregar reparación: {e}")
            conn.rollback()
            return None
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al agregar reparación: {e}")
            conn.rollback()
            return None
        finally:
            if conn: conn.close()
    return None

def obtener_historial_reparaciones_vehiculo(vehiculo_id):
    conn = obtener_conexion()
    historial = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id, r.fecha_ingreso, r.fecha_salida, r.kilometraje_ingreso, r.kilometraje_salida,
                       r.problema_reportado, r.trabajos_realizados, r.repuestos_usados, r.costo_mano_obra, r.costo_total, r.estado,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente, c.id AS cliente_id, v.marca, v.modelo, v.anio, v.patente,
                       r.turno_origen_id
                FROM reparaciones r
                LEFT JOIN mecanicos m ON r.mecanico_id = m.id
                JOIN vehiculos v ON r.vehiculo_id = v.id 
                JOIN clientes c ON v.cliente_id = c.id
                WHERE r.vehiculo_id = %s 
                ORDER BY r.fecha_ingreso DESC, r.id DESC
            ''', (vehiculo_id,))
            raw_historial = cursor.fetchall()
            if isinstance(conn, psycopg2.extensions.connection):
                historial = [_map_row_to_dict(cursor, row) for row in raw_historial]
            else:
                historial = [dict(row) for row in raw_historial]
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener historial de reparaciones para vehículo {vehiculo_id}: {e}")
        finally:
            if conn: conn.close()
    return historial

def obtener_reparacion_por_id(reparacion_id):
    conn = obtener_conexion()
    reparacion = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id, r.vehiculo_id, r.mecanico_id, r.fecha_ingreso, r.fecha_salida, r.kilometraje_ingreso, r.kilometraje_salida,
                       r.problema_reportado, r.trabajos_realizados, r.repuestos_usados, r.costo_mano_obra, r.costo_total, r.estado, r.turno_origen_id,
                       v.patente, v.marca, v.modelo, v.anio, v.cliente_id,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente, c.dni AS dni_cliente
                FROM reparaciones r
                JOIN vehiculos v ON r.vehiculo_id = v.id 
                JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN mecanicos m ON r.mecanico_id = m.id
                WHERE r.id = %s
            ''', (reparacion_id,))
            raw_reparacion = cursor.fetchone()
            if raw_reparacion:
                if isinstance(conn, psycopg2.extensions.connection):
                    reparacion = _map_row_to_dict(cursor, raw_reparacion)
                else:
                    reparacion = dict(raw_reparacion)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener reparación por ID {reparacion_id}: {e}")
        finally:
            if conn: conn.close()
    return reparacion

def actualizar_estado_reparacion(reparacion_id, estado, trabajos_realizados=None, repuestos_usados=None, costo_mano_obra=None, costo_total=None, fecha_salida=None, kilometraje_salida=None):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            update_query = '''
                UPDATE reparaciones
                SET estado = %s
            '''
            params = [estado]

            if trabajos_realizados is not None:
                update_query += ', trabajos_realizados = %s'
                params.append(trabajos_realizados)
            if repuestos_usados is not None:
                update_query += ', repuestos_usados = %s'
                params.append(repuestos_usados)
            if costo_mano_obra is not None:
                update_query += ', costo_mano_obra = %s'
                params.append(costo_mano_obra)
            if costo_total is not None:
                update_query += ', costo_total = %s'
                params.append(costo_total)
            if fecha_salida is not None:
                update_query += ', fecha_salida = %s'
                params.append(fecha_salida)
            if kilometraje_salida is not None:
                update_query += ', kilometraje_salida = %s'
                params.append(kilometraje_salida)

            update_query += ' WHERE id = %s'
            params.append(reparacion_id)

            cursor.execute(update_query, tuple(params))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al actualizar estado de reparación {reparacion_id}: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def obtener_reparacion_activa_por_vehiculo(vehiculo_id):
    conn = obtener_conexion()
    reparacion_activa = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id, r.vehiculo_id, r.mecanico_id, r.fecha_ingreso, r.kilometraje_ingreso,
                       r.problema_reportado, r.trabajos_realizados, r.repuestos_usados, r.costo_mano_obra, r.costo_total, r.estado,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico,
                       v.patente, v.marca, v.modelo
                FROM reparaciones r
                LEFT JOIN mecanicos m ON r.mecanico_id = m.id
                JOIN vehiculos v ON r.vehiculo_id = v.id 
                WHERE r.vehiculo_id = %s AND r.estado IN ('En Progreso', 'Pendiente', 'En Espera de Piezas') 
                ORDER BY r.fecha_ingreso DESC
                LIMIT 1
            ''', (vehiculo_id,))
            raw_reparacion = cursor.fetchone()
            if raw_reparacion:
                if isinstance(conn, psycopg2.extensions.connection):
                    reparacion_activa = _map_row_to_dict(cursor, raw_reparacion)
                else:
                    reparacion_activa = dict(raw_reparacion)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener reparación activa para vehículo {vehiculo_id}: {e}")
        finally:
            if conn: conn.close()
    return reparacion_activa

def obtener_vehiculos_en_taller():
    """
    Obtiene todos los vehículos que tienen una reparación con estado 'En Progreso', 'Pendiente' o 'En Espera de Piezas'.
    """
    conn = obtener_conexion()
    vehiculos_en_taller = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id AS reparacion_id, v.id AS vehiculo_id, v.patente, v.marca, v.modelo, v.anio, v.kilometraje_inicial,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente,
                       r.estado AS estado_reparacion, r.problema_reportado,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico,
                       r.fecha_ingreso AS fecha_ingreso_taller,
                       r.turno_origen_id
                FROM reparaciones r
                JOIN vehiculos v ON r.vehiculo_id = v.id 
                JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN mecanicos m ON r.mecanico_id = m.id
                WHERE r.estado IN ('En Progreso', 'Pendiente', 'En Espera de Piezas')
                ORDER BY 
                    CASE r.estado 
                        WHEN 'En Progreso' THEN 1
                        WHEN 'Pendiente' THEN 2
                        WHEN 'En Espera de Piezas' THEN 3
                        ELSE 4 
                    END,
                    r.fecha_ingreso DESC
            ''')
            raw_data = cursor.fetchall()
            if isinstance(conn, psycopg2.extensions.connection):
                vehiculos_en_taller = [_map_row_to_dict(cursor, row) for row in raw_data]
            else:
                vehiculos_en_taller = [dict(row) for row in raw_data]
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener vehículos en taller: {e}")
        finally:
            if conn: conn.close()
    return vehiculos_en_taller

# Función para crear una reparación a partir de un turno
def crear_reparacion_desde_turno(turno_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            turno = obtener_turno_por_id(turno_id) 
            if not turno:
                print(f"Turno con ID {turno_id} no encontrado para crear reparación.")
                return None

            # Verificar si ya existe una reparación para este turno para evitar duplicados
            # Nota: Para Psycopg2, fetchone() devuelve una tupla, así que accedemos a [0]
            # Para SQLite, si row_factory es Row, se puede acceder como dict, pero fetchone()[0] también funciona para el primer elemento
            cursor.execute('SELECT id FROM reparaciones WHERE turno_origen_id = %s', (turno_id,))
            existing_reparacion = cursor.fetchone()
            if existing_reparacion:
                print(f"Advertencia: Ya existe una reparación (ID: {existing_reparacion[0]}) para el turno {turno_id}.")
                return existing_reparacion[0]

            vehiculo = obtener_vehiculo_por_id(turno['vehiculo_id']) 
            kilometraje_ingreso_reparacion = vehiculo['kilometraje_inicial'] if vehiculo else 0

            cursor.execute('''
                INSERT INTO reparaciones (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, estado, turno_origen_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (turno['vehiculo_id'], turno['mecanico_id'], turno['fecha'],
                  kilometraje_ingreso_reparacion, 
                  turno['problema_reportado'], 'En Progreso', turno_id))
            
            reparacion_id = cursor.fetchone()[0] # Obtener ID para PostgreSQL

            # Actualizar el estado del turno a 'Completado'
            cursor.execute('UPDATE turnos SET estado = %s WHERE id = %s', ('Completado', turno_id))
            
            conn.commit()
            return reparacion_id
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            print(f"Error al crear reparación desde turno {turno_id}: {e}")
            conn.rollback()
            return None
        except Exception as e: # Captura cualquier otra excepción general
            print(f"Error inesperado al crear reparación desde turno {turno_id}: {e}")
            conn.rollback()
            return None
        finally:
            if conn: conn.close()
    return None

