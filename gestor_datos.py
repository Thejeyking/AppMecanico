import sqlite3
import bcrypt
import os

from flask import app # Asegúrate de que esto no cause un error si 'app' no está disponible globalmente
import psycopg2
from psycopg2 import Error as Psycopg2Error

DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE_FILE = 'taller_mecanico.db'

def obtener_conexion():
    """Establece y devuelve una conexión a la base de datos (PostgreSQL o SQLite)."""
    conn = None
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print("DEBUG DB: Conectado a PostgreSQL.")
        except Psycopg2Error as e:
            print(f"Error al conectar a PostgreSQL: {e}")
            conn = None
    else:
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            conn.row_factory = sqlite3.Row # Esto ya debería permitir acceso por nombre
            print("DEBUG DB: Conectado a SQLite.")
        except sqlite3.Error as e:
            print(f"Error al conectar a SQLite: {e}")
            conn = None
    return conn

def crear_tablas():
    """
    Crea las tablas necesarias en la base de datos si no existen.
    Adapta la sintaxis SQL para PostgreSQL o SQLite según la conexión activa.
    """
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            # Define el tipo de ID auto-incremental según la base de datos
            if is_postgresql:
                id_type_sql = 'SERIAL PRIMARY KEY' # ¡CORRECCIÓN CLAVE para PostgreSQL!
            else:
                id_type_sql = 'INTEGER PRIMARY KEY AUTOINCREMENT' # Para SQLite

            # Tabla Clientes
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS clientes (
                    id {id_type_sql},
                    nombre VARCHAR(255) NOT NULL,
                    apellido VARCHAR(255) NOT NULL,
                    telefono VARCHAR(50),
                    email VARCHAR(255),
                    dni VARCHAR(50) UNIQUE
                )
            ''')

            # Tabla Usuarios_Clientes
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS usuarios_clientes (
                    id {id_type_sql},
                    cliente_id INT UNIQUE NOT NULL,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Mecanicos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS mecanicos (
                    id {id_type_sql},
                    nombre VARCHAR(255) NOT NULL,
                    apellido VARCHAR(255) NOT NULL,
                    telefono VARCHAR(50),
                    email VARCHAR(255)
                )
            ''')

            # Tabla Usuarios_Mecanicos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS usuarios_mecanicos (
                    id {id_type_sql},
                    mecanico_id INT UNIQUE NOT NULL,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Vehiculos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS vehiculos (
                    id {id_type_sql},
                    cliente_id INT NOT NULL,
                    patente VARCHAR(50) UNIQUE NOT NULL,
                    marca VARCHAR(255) NOT NULL,
                    modelo VARCHAR(255) NOT NULL,
                    anio INT,
                    kilometraje_inicial INT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Turnos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS turnos (
                    id {id_type_sql},
                    cliente_id INT NOT NULL,
                    vehiculo_id INT NOT NULL,
                    mecanico_id INT,
                    fecha VARCHAR(50) NOT NULL,
                    hora VARCHAR(50) NOT NULL,
                    problema_reportado TEXT NOT NULL,
                    estado VARCHAR(50) NOT NULL DEFAULT 'Agendado',
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
                    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE SET NULL
                )
            ''')

            # Tabla Reparaciones
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS reparaciones (
                    id {id_type_sql},
                    vehiculo_id INT NOT NULL,
                    mecanico_id INT,
                    fecha_ingreso VARCHAR(50) NOT NULL,
                    fecha_salida VARCHAR(50),
                    kilometraje_ingreso INT NOT NULL,
                    kilometraje_salida INT,
                    problema_reportado TEXT,
                    trabajos_realizados TEXT,
                    repuestos_usados TEXT,
                    costo_mano_obra DECIMAL(10, 2),
                    costo_total DECIMAL(10, 2),
                    estado VARCHAR(50) NOT NULL DEFAULT 'En Progreso',
                    turno_origen_id INT UNIQUE,
                    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE SET NULL,
                    FOREIGN KEY (turno_origen_id) REFERENCES turnos(id) ON DELETE SET NULL
                )
            ''')

            conn.commit()
            print("Base de datos inicializada o verificada correctamente.")
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al crear tablas: {e}")
        finally:
            if conn:
                conn.close()

# --- Funciones auxiliares (adaptadas para PostgreSQL) ---
def _map_row_to_dict(cursor, row):
    """Mapea una fila de resultados a un diccionario."""
    if not row:
        return None
    # Asegúrate de que el row_factory esté configurado para devolver diccionarios o mapea manualmente
    # Para psycopg2, si no se usa DictCursor, devuelve tuplas.
    # Para sqlite3, si se usa row_factory = sqlite3.Row, devuelve objetos Row accesibles como diccionarios.
    # Esta lógica es genérica para ambos si cursor.description es consistente.
    columns = [desc[0] for desc in cursor.description]
    return {col_name: row[i] for i, col_name in enumerate(columns)}

def _get_param_placeholder(conn):
    """Auxiliar para obtener el marcador de posición correcto para la base de datos."""
    # PostgreSQL y Psycopg2 usan %s
    # SQLite usa ?
    return '%s' if isinstance(conn, psycopg2.extensions.connection) else '?'

def _obtener_cliente_por_dni(conn, dni):
    """
    Función auxiliar para obtener un cliente por su DNI.
    Recibe la conexión para ser usada dentro de una transacción existente.
    """
    cliente = None
    try:
        cursor = conn.cursor()
        placeholder = _get_param_placeholder(conn)
	# ### DEBUG ###
        print(f"### DEBUG _obtener_cliente_por_dni: Buscando DNI: {dni}")
        cursor.execute(f'SELECT id, nombre, apellido, telefono, email, dni FROM clientes WHERE dni = {placeholder}', (dni,))
        raw_cliente = cursor.fetchone()
        if raw_cliente:
                cliente = _map_row_to_dict(cursor, raw_cliente)
                # ### DEBUG ###
                print(f"### DEBUG _obtener_cliente_por_dni: DNI {dni} ENCONTRADO. Cliente ID: {cliente['id']}")
        else:
                # ### DEBUG ###
                print(f"### DEBUG _obtener_cliente_por_dni: DNI {dni} NO ENCONTRADO.")
    except (sqlite3.Error, Psycopg2Error) as e:
        print(f"Error en _obtener_cliente_por_dni: {e}")
        # No se hace rollback aquí, ya que esta función es auxiliar y la transacción se maneja externamente
    return cliente

# --- FUNCIÓN AUXILIAR FALTANTE: _obtener_usuario_cliente_por_cliente_id ---
def _obtener_usuario_cliente_por_cliente_id(conn, cliente_id):
    """
    Función auxiliar para obtener un usuario_cliente por su cliente_id.
    """
    usuario = None
    try:
        cursor = conn.cursor()
        placeholder = _get_param_placeholder(conn)
        cursor.execute(f'SELECT id, username, cliente_id FROM usuarios_clientes WHERE cliente_id = {placeholder}', (cliente_id,))
        raw_usuario = cursor.fetchone()
        if raw_usuario:
            usuario = _map_row_to_dict(cursor, raw_usuario)
    except (sqlite3.Error, Psycopg2Error) as e:
        print(f"Error en _obtener_usuario_cliente_por_cliente_id: {e}")
    return usuario

# --- FUNCIÓN AUXILIAR FALTANTE: _obtener_usuario_cliente_por_username ---
def _obtener_usuario_cliente_por_username(conn, username):
    """
    Función auxiliar para obtener un usuario_cliente por su nombre de usuario.
    """
    usuario = None
    try:
        cursor = conn.cursor()
        placeholder = _get_param_placeholder(conn)
        cursor.execute(f'SELECT id, username, cliente_id FROM usuarios_clientes WHERE username = {placeholder}', (username,))
        raw_usuario = cursor.fetchone()
        if raw_usuario:
            usuario = _map_row_to_dict(cursor, raw_usuario)
    except (sqlite3.Error, Psycopg2Error) as e:
        print(f"Error en _obtener_usuario_cliente_por_username: {e}")
    return usuario


# MODIFICACIÓN CLAVE: _get_inserted_id ahora no se usa directamente para PostgreSQL,
# en su lugar, la función que hace el INSERT leerá el ID de cursor.fetchone()
# después de un INSERT ... RETURNING id.
# Mantendremos la función para compatibilidad con SQLite si es necesario,
# pero las funciones de inserción se adaptarán.

# --- Funciones de Gestión de Clientes ---
def agregar_cliente(nombre, apellido, telefono, email, dni):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            placeholder = _get_param_placeholder(conn)
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            query = f'''
                INSERT INTO clientes (nombre, apellido, telefono, email, dni)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                query += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(query, (nombre, apellido, telefono, email, dni))
            
            if is_postgresql:
                cliente_id = cursor.fetchone()[0] # Obtener el ID de RETURNING
            else:
                cliente_id = cursor.lastrowid # Para SQLite

            conn.commit()
            return cliente_id
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            print(f"Error al agregar cliente: {e}")
            conn.rollback()
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
            clientes = [_map_row_to_dict(cursor, row) for row in raw_clientes]
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'SELECT id, nombre, apellido, telefono, email, dni FROM clientes WHERE id = {placeholder}', (cliente_id,))
            raw_cliente = cursor.fetchone()
            if raw_cliente:
                cliente = _map_row_to_dict(cursor, raw_cliente)
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT c.id, c.nombre, c.apellido, c.telefono, c.email, c.dni, uc.username, uc.id AS usuario_cliente_id
                FROM clientes c
                JOIN usuarios_clientes uc ON c.id = uc.cliente_id
                WHERE uc.username = {placeholder}
            ''', (username,))
            raw_cliente = cursor.fetchone()
            if raw_cliente:
                cliente_data = _map_row_to_dict(cursor, raw_cliente)
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                UPDATE clientes
                SET nombre = {placeholder}, apellido = {placeholder}, telefono = {placeholder}, email = {placeholder}, dni = {placeholder}
                WHERE id = {placeholder}
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'DELETE FROM clientes WHERE id = {placeholder}', (cliente_id,))
            conn.commit()
            return True
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al eliminar cliente: {e}")
            conn.rollback()
            return False
        finally:
            if conn: conn.close()
    return False

def obtener_cliente_por_nombre_apellido(nombre, apellido):
    conn = obtener_conexion()
    cliente = None
    if conn:
        try:
            cursor = conn.cursor()
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'SELECT id, nombre, apellido, telefono, email, dni FROM clientes WHERE nombre = {placeholder} AND apellido = {placeholder}', (nombre, apellido))
            raw_cliente = cursor.fetchone()
            if raw_cliente:
                cliente = _map_row_to_dict(cursor, raw_cliente)
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener cliente por nombre y apellido: {e}")
        finally:
            if conn: conn.close()
    return cliente

def registrar_cliente_con_usuario(nombre, apellido, username, password, dni):
    conn = obtener_conexion()
    if not conn:
	# ### DEBUG ###
        print("### DEBUG registrar_cliente_con_usuario: NO SE PUDO OBTENER CONEXIÓN A LA DB.")
        return False, "Error de conexión a la base de datos."

    try:
        placeholder = _get_param_placeholder(conn)
        is_postgresql = isinstance(conn, psycopg2.extensions.connection)

	# ### DEBUG ###
        print(f"### DEBUG registrar_cliente_con_usuario: Intentando registrar cliente: {nombre} {apellido}, DNI: {dni}, User: {username}")

        cliente_existente_por_dni = _obtener_cliente_por_dni(conn, dni)
        if cliente_existente_por_dni:
            ### DEBUG ###
            print(f"### DEBUG registrar_cliente_con_usuario: Cliente con DNI {dni} YA EXISTE. ID: {cliente_existente_por_dni['id']}")
            usuario_existente_para_cliente = _obtener_usuario_cliente_por_cliente_id(conn, cliente_existente_por_dni['id'])
            if usuario_existente_para_cliente:
                return False, "Ya existe una cuenta asociada a este DNI. Por favor, inicia sesión."
            else:
                if _obtener_usuario_cliente_por_username(conn, username):
                    return False, "El nombre de usuario propuesto ya está en uso."

                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor = conn.cursor()
                query_insert_user = f'''
                    INSERT INTO usuarios_clientes (cliente_id, username, password)
                    VALUES ({placeholder}, {placeholder}, {placeholder})
                '''
                if is_postgresql:
                    query_insert_user += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!
		# ### DEBUG ###
                print(f"### DEBUG registrar_cliente_con_usuario: Ejecutando INSERT de usuario para cliente ID {cliente_existente_por_dni['id']}")

                cursor.execute(query_insert_user, (cliente_existente_por_dni['id'], username, hashed_password))


                # No necesitamos el ID del usuario_cliente para este flujo, pero lo obtenemos si se usa RETURNING
                if is_postgresql:
                    _ = cursor.fetchone()[0] # Consumir el resultado de RETURNING si existe

                conn.commit()
                return True, "Cuenta creada y asociada a su DNI existente. Ahora puedes iniciar sesión."
        else:
            if _obtener_usuario_cliente_por_username(conn, username):
                return False, "El nombre de usuario ya existe. Por favor, elige otro."

            cursor = conn.cursor()
            insert_cliente_sql = f'''
                INSERT INTO clientes (nombre, apellido, dni)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                insert_cliente_sql += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(insert_cliente_sql, (nombre, apellido, dni))
            
            if is_postgresql:
                cliente_id = cursor.fetchone()[0] # Obtener el ID de RETURNING
            else:
                cliente_id = cursor.lastrowid # Para SQLite

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            query_insert_user = f'''
                INSERT INTO usuarios_clientes (cliente_id, username, password)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                query_insert_user += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(query_insert_user, (cliente_id, username, hashed_password))
            
            if is_postgresql:
                _ = cursor.fetchone()[0] # Consumir el resultado de RETURNING si existe

            conn.commit()
            return True, "Registro exitoso. ¡Bienvenido! Ya puedes iniciar sesión."

    except (sqlite3.IntegrityError, Psycopg2Error) as e:
        conn.rollback()
        error_message = str(e).lower()
        if "duplicate entry" in error_message or "unique constraint" in error_message: # Adaptado para mensajes de error de PostgreSQL
            if "username" in error_message:
                return False, "El nombre de usuario ya está registrado."
            elif "dni" in error_message:
                return False, "El DNI ya está registrado por otro cliente."
        print(f"Error de integridad en registrar_cliente_con_usuario: {e}")
        return False, f"Error al registrar: {e}"
    except Exception as e:
        conn.rollback()
        print(f"Error inesperado en registrar_cliente_con_usuario: {e}")
        return False, f"Error inesperado al registrar: {e}"
    finally:
        if conn:
            conn.close()


def verificar_credenciales_cliente(username, password):
    conn = obtener_conexion()
    cliente_data = None
    if conn:
        try:
            cursor = conn.cursor()
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'SELECT uc.password, c.id AS cliente_id, uc.id AS usuario_cliente_id, uc.username FROM usuarios_clientes uc JOIN clientes c ON uc.cliente_id = c.id WHERE uc.username = {placeholder}', (username,))
            user_record_raw = cursor.fetchone()

            if user_record_raw:
                user_record = _map_row_to_dict(cursor, user_record_raw)
                stored_hashed_password = user_record['password'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
                    cliente_data = user_record
                    del cliente_data['password']
            else:
                print(f"DEBUG: No se encontró usuario '{username}'.")
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al verificar credenciales de cliente: {e}")
        finally:
            if conn: conn.close()
    return cliente_data


# --- Funciones de Gestión de Mecánicos ---
def agregar_mecanico(nombre, apellido, telefono, email, username, password):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            placeholder = _get_param_placeholder(conn)
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            query_mecanico = f'''
                INSERT INTO mecanicos (nombre, apellido, telefono, email)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                query_mecanico += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(query_mecanico, (nombre, apellido, telefono, email))
            
            if is_postgresql:
                mecanico_id = cursor.fetchone()[0] # Obtener el ID de RETURNING
            else:
                mecanico_id = cursor.lastrowid # Para SQLite

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            query_user_mecanico = f'''
                INSERT INTO usuarios_mecanicos (mecanico_id, username, password)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                query_user_mecanico += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(query_user_mecanico, (mecanico_id, username, hashed_password))
            
            if is_postgresql:
                _ = cursor.fetchone()[0] # Consumir el resultado de RETURNING si existe

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
            mecanicos = [_map_row_to_dict(cursor, row) for row in raw_mecanicos]
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'SELECT id, nombre, apellido, telefono, email FROM mecanicos WHERE id = {placeholder}', (mecanico_id,))
            raw_mecanico = cursor.fetchone()
            if raw_mecanico:
                mecanico = _map_row_to_dict(cursor, raw_mecanico)
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                UPDATE mecanicos
                SET nombre = {placeholder}, apellido = {placeholder}, telefono = {placeholder}, email = {placeholder}
                WHERE id = {placeholder}
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'DELETE FROM mecanicos WHERE id = {placeholder}', (mecanico_id,))
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT
                    um.password,
                    m.id AS mecanico_id,
                    m.nombre,
                    m.apellido,
                    m.telefono,
                    m.email
                FROM usuarios_mecanicos um
                JOIN mecanicos m ON um.mecanico_id = m.id
                WHERE um.username = {placeholder}
            ''', (username,))
            user_record_raw = cursor.fetchone()

            if user_record_raw:
                user_record = _map_row_to_dict(cursor, user_record_raw)
                user_record['id'] = user_record['mecanico_id']
                stored_hashed_password = user_record['password'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
                    mecanico_data = user_record
                    del mecanico_data['password']
                else:
                    print(f"DEBUG: Contraseña incorrecta para usuario '{username}'.")
            else:
                print(f"DEBUG: No se encontró mecánico con usuario '{username}'.")

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
            placeholder = _get_param_placeholder(conn)
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            query = f'''
                INSERT INTO vehiculos (cliente_id, patente, marca, modelo, anio, kilometraje_inicial)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                query += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(query, (cliente_id, patente, marca, modelo, anio, kilometraje_inicial))
            
            if is_postgresql:
                vehiculo_id = cursor.fetchone()[0] # Obtener el ID de RETURNING
            else:
                vehiculo_id = cursor.lastrowid # Para SQLite

            conn.commit()
            return vehiculo_id # Devolver el ID del vehículo
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT v.id, v.cliente_id, v.patente, v.marca, v.modelo, v.anio, v.kilometraje_inicial,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente
                FROM vehiculos v
                JOIN clientes c ON v.cliente_id = c.id
                WHERE v.cliente_id = {placeholder}
                ORDER BY v.patente
            ''', (cliente_id,))
            raw_vehiculos = cursor.fetchall()
            vehiculos = [_map_row_to_dict(cursor, row) for row in raw_vehiculos]
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT v.id, v.cliente_id, v.patente, v.marca, v.modelo, v.anio, v.kilometraje_inicial,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente
                FROM vehiculos v
                JOIN clientes c ON v.cliente_id = c.id
                WHERE v.id = {placeholder}
            ''', (vehiculo_id,))
            raw_vehiculo = cursor.fetchone()
            if raw_vehiculo:
                vehiculo = _map_row_to_dict(cursor, raw_vehiculo)
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                UPDATE vehiculos
                SET marca = {placeholder}, modelo = {placeholder}, anio = {placeholder}, patente = {placeholder}, kilometraje_inicial = {placeholder}
                WHERE id = {placeholder}
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'DELETE FROM vehiculos WHERE id = {placeholder}', (vehiculo_id,))
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
            placeholder = _get_param_placeholder(conn)
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            query = f'''
                INSERT INTO turnos (cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, estado)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                query += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(query, (cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, 'Agendado'))
            
            if is_postgresql:
                turno_id = cursor.fetchone()[0] # Obtener el ID de RETURNING
            else:
                turno_id = cursor.lastrowid # Para SQLite

            conn.commit()
            return turno_id # Devolver el ID del turno
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
            turnos = [_map_row_to_dict(cursor, row) for row in raw_turnos]
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT t.id, t.cliente_id, t.vehiculo_id, t.mecanico_id, t.fecha, t.hora, t.problema_reportado, t.estado,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente, c.dni, c.telefono, c.email,
                       v.patente, v.marca AS marca_vehiculo, v.modelo AS modelo_vehiculo, v.anio AS anio_vehiculo,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico
                FROM turnos t
                JOIN clientes c ON t.cliente_id = c.id
                JOIN vehiculos v ON t.vehiculo_id = v.id
                LEFT JOIN mecanicos m ON t.mecanico_id = m.id
                WHERE t.id = {placeholder}
            ''', (turno_id,))
            raw_turno = cursor.fetchone()
            if raw_turno:
                turno = _map_row_to_dict(cursor, raw_turno)
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                UPDATE turnos
                SET cliente_id = {placeholder}, vehiculo_id = {placeholder}, mecanico_id = {placeholder}, fecha = {placeholder}, hora = {placeholder}, problema_reportado = {placeholder}, estado = {placeholder}
                WHERE id = {placeholder}
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'DELETE FROM turnos WHERE id = {placeholder}', (turno_id,))
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
            placeholder = _get_param_placeholder(conn)
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            query = f'''
                INSERT INTO reparaciones (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, estado, turno_origen_id)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                query += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(query, (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, 'En Progreso', turno_origen_id))
            
            if is_postgresql:
                reparacion_id = cursor.fetchone()[0] # Obtener el ID de RETURNING
            else:
                reparacion_id = cursor.lastrowid # Para SQLite

            conn.commit()
            return reparacion_id
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            if "duplicate entry" in str(e).lower() or "unique constraint" in str(e).lower(): # Adaptado para PostgreSQL
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT r.id, r.fecha_ingreso, r.fecha_salida, r.kilometraje_ingreso, r.kilometraje_salida,
                       r.problema_reportado, r.trabajos_realizados, r.repuestos_usados, r.costo_mano_obra, r.costo_total, r.estado,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente, c.id AS cliente_id, v.marca, v.modelo, v.anio, v.patente,
                       r.turno_origen_id
                FROM reparaciones r
                LEFT JOIN mecanicos m ON r.mecanico_id = m.id
                JOIN vehiculos v ON r.vehiculo_id = v.id
                JOIN clientes c ON v.cliente_id = c.id
                WHERE r.vehiculo_id = {placeholder}
                ORDER BY r.fecha_ingreso DESC, r.id DESC
            ''', (vehiculo_id,))
            raw_historial = cursor.fetchall()
            historial = [_map_row_to_dict(cursor, row) for row in raw_historial]
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT r.id, r.vehiculo_id, r.mecanico_id, r.fecha_ingreso, r.fecha_salida, r.kilometraje_ingreso, r.kilometraje_salida,
                       r.problema_reportado, r.trabajos_realizados, r.repuestos_usados, r.costo_mano_obra, r.costo_total, r.estado, r.turno_origen_id,
                       v.patente, v.marca, v.modelo, v.anio, v.cliente_id,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico,
                       c.nombre AS nombre_cliente, c.apellido AS apellido_cliente, c.dni AS dni_cliente
                FROM reparaciones r
                JOIN vehiculos v ON r.vehiculo_id = v.id
                JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN mecanicos m ON r.mecanico_id = m.id
                WHERE r.id = {placeholder}
            ''', (reparacion_id,))
            raw_reparacion = cursor.fetchone()
            if raw_reparacion:
                reparacion = _map_row_to_dict(cursor, raw_reparacion)
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
            placeholder = _get_param_placeholder(conn)

            update_query = f'''
                UPDATE reparaciones
                SET estado = {placeholder}
            '''
            params = [estado]

            if trabajos_realizados is not None:
                update_query += f', trabajos_realizados = {placeholder}'
                params.append(trabajos_realizados)
            if repuestos_usados is not None:
                update_query += f', repuestos_usados = {placeholder}'
                params.append(repuestos_usados)
            if costo_mano_obra is not None:
                update_query += f', costo_mano_obra = {placeholder}'
                params.append(costo_mano_obra)
            if costo_total is not None:
                update_query += f', costo_total = {placeholder}'
                params.append(costo_total)
            if fecha_salida is not None:
                update_query += f', fecha_salida = {placeholder}'
                params.append(fecha_salida)
            if kilometraje_salida is not None:
                update_query += f', kilometraje_salida = {placeholder}'
                params.append(kilometraje_salida)

            update_query += f' WHERE id = {placeholder}'
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
            placeholder = _get_param_placeholder(conn)
            cursor.execute(f'''
                SELECT r.id, r.vehiculo_id, r.mecanico_id, r.fecha_ingreso, r.kilometraje_ingreso,
                       r.problema_reportado, r.trabajos_realizados, r.repuestos_usados, r.costo_mano_obra, r.costo_total, r.estado,
                       m.nombre AS nombre_mecanico, m.apellido AS apellido_mecanico,
                       v.patente, v.marca, v.modelo
                FROM reparaciones r
                LEFT JOIN mecanicos m ON r.mecanico_id = m.id
                JOIN vehiculos v ON r.vehiculo_id = v.id
                WHERE r.vehiculo_id = {placeholder} AND r.estado IN ('En Progreso', 'Pendiente', 'En Espera de Piezas')
                ORDER BY r.fecha_ingreso DESC
                LIMIT 1
            ''', (vehiculo_id,))
            raw_reparacion = cursor.fetchone()
            if raw_reparacion:
                reparacion_activa = _map_row_to_dict(cursor, raw_reparacion)
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
            vehiculos_en_taller = [_map_row_to_dict(cursor, row) for row in raw_data]
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al obtener vehículos en taller: {e}")
        finally:
            if conn:
                conn.close()
    return vehiculos_en_taller

def crear_reparacion_desde_turno(turno_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            placeholder = _get_param_placeholder(conn)
            is_postgresql = isinstance(conn, psycopg2.extensions.connection)

            turno = obtener_turno_por_id(turno_id)
            if not turno:
                print(f"Turno con ID {turno_id} no encontrado para crear reparación.")
                return None

            cursor.execute(f'SELECT id FROM reparaciones WHERE turno_origen_id = {placeholder}', (turno_id,))
            existing_reparacion = cursor.fetchone()
            if existing_reparacion:
                print(f"Advertencia: Ya existe una reparación (ID: {existing_reparacion[0]}) para el turno {turno_id}.")
                return existing_reparacion[0] # Devolver el ID existente

            vehiculo = obtener_vehiculo_por_id(turno['vehiculo_id'])
            kilometraje_ingreso_reparacion = vehiculo['kilometraje_inicial'] if vehiculo else 0

            insert_repair_query = f'''
                INSERT INTO reparaciones (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, estado, turno_origen_id)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if is_postgresql:
                insert_repair_query += ' RETURNING id' # ¡CORRECCIÓN CLAVE para PostgreSQL!

            cursor.execute(insert_repair_query, (turno['vehiculo_id'], turno['mecanico_id'], turno['fecha'],
                                                 kilometraje_ingreso_reparacion,
                                                 turno['problema_reportado'], 'En Progreso', turno_id))

            if is_postgresql:
                reparacion_id = cursor.fetchone()[0] # Obtener el ID de RETURNING
            else:
                reparacion_id = cursor.lastrowid # Para SQLite

            cursor.execute(f'UPDATE turnos SET estado = {placeholder} WHERE id = {placeholder}', ('Completado', turno_id))

            conn.commit()
            return reparacion_id
        except (sqlite3.IntegrityError, Psycopg2Error) as e:
            if "duplicate entry" in str(e).lower() or "unique constraint" in str(e).lower(): # Adaptado para PostgreSQL
                print(f"Error: Intento de crear reparación duplicada para turno {turno_id}. Ya existe.")
            else:
                print(f"Error de integridad al agregar reparación desde turno {turno_id}: {e}")
            conn.rollback()
            return None
        except (sqlite3.Error, Psycopg2Error) as e:
            print(f"Error al crear reparación desde turno {turno_id}: {e}")
            conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    return None

if __name__ == '__main__':
    crear_tablas()
    pass
