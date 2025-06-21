import sqlite3
import bcrypt
import os

from flask import app
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

            id_type_sql = 'SERIAL' if is_postgresql else 'INTEGER PRIMARY KEY AUTOINCREMENT'
            
            # Tabla Clientes
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS clientes (
                    id {id_type_sql},
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    dni TEXT UNIQUE
                )
            ''')

            # Tabla Usuarios_Clientes
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS usuarios_clientes (
                    id {id_type_sql},
                    cliente_id INTEGER UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Mecanicos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS mecanicos (
                    id {id_type_sql},
                    nombre TEXT NOT NULL,
                    apellido TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT
                )
            ''')

            # Tabla Usuarios_Mecanicos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS usuarios_mecanicos (
                    id {id_type_sql},
                    mecanico_id INTEGER UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE CASCADE
                )
            ''')

            # Tabla Vehiculos
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS vehiculos (
                    id {id_type_sql},
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
                    id {id_type_sql},
                    cliente_id INTEGER NOT NULL,
                    vehiculo_id INTEGER NOT NULL,
                    mecanico_id INTEGER,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    problema_reportado TEXT NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'Agendado',
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
                    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE CASCADE,
                    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id) ON DELETE SET NULL
                )
            ''')

            # Tabla Reparaciones
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS reparaciones (
                    id {id_type_sql},
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
                    estado TEXT NOT NULL DEFAULT 'En Progreso',
                    turno_origen_id INTEGER UNIQUE,
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

def _map_row_to_dict(cursor, row):
    """
    Mapea una tupla de resultados de Psycopg2 o una fila de SQLite a un diccionario.
    Maneja el caso donde los nombres de las columnas pueden colisionar en joins (ej. 'id').
    """
    if not row:
        return None
    
    # Obtener los nombres de las columnas del cursor.description
    # cursor.description es una lista de tuplas (name, type_code, display_size, internal_size, precision, scale, null_ok)
    columns = [desc[0] for desc in cursor.description]
    
    # Crear el diccionario. Si hay nombres de columna duplicados (ej. 'id'),
    # el último valor sobrescribirá al anterior, lo cual es el comportamiento deseado
    # si los aliases no se usaron bien en la consulta SQL.
    # Esto es una alternativa a sqlite3.Row si los resultados no se obtienen directamente como Row.
    result_dict = {}
    for i, col_name in enumerate(columns):
        result_dict[col_name] = row[i]
    return result_dict


# Auxiliar para obtener el marcador de posición correcto
def _get_param_placeholder(conn):
    return '%s' if isinstance(conn, psycopg2.extensions.connection) else '?'

# Auxiliar para obtener el ID de una inserción (maneja RETURNING para Pg, lastrowid para SQLite)
def _get_inserted_id(conn, cursor):
    if isinstance(conn, psycopg2.extensions.connection):
        return cursor.fetchone()[0]
    else:
        return cursor.lastrowid

# --- Funciones de Gestión de Clientes ---
def agregar_cliente(nombre, apellido, telefono, email, dni):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            placeholder = _get_param_placeholder(conn)
            
            query = f'''
                INSERT INTO clientes (nombre, apellido, telefono, email, dni)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if isinstance(conn, psycopg2.extensions.connection):
                query += ' RETURNING id'

            cursor.execute(query, (nombre, apellido, telefono, email, dni))
            cliente_id = _get_inserted_id(conn, cursor)
            
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

# Funciones de cliente_app (registro y login de clientes)
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

###################################################################################################
'''
def _map_row_to_dict(cursor, row):
    """Mapea una fila de resultados a un diccionario."""
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description]
    return {col_name: row[i] for i, col_name in enumerate(columns)}

def _get_param_placeholder(conn):
    """Auxiliar para obtener el marcador de posición correcto para la base de datos."""
    return '%s' if isinstance(conn, psycopg2.extensions.connection) else '?'

def _get_inserted_id(conn, cursor):
    """Auxiliar para obtener el ID de una inserción (maneja RETURNING para Pg, lastrowid para SQLite)."""
    if isinstance(conn, psycopg2.extensions.connection):
        return cursor.fetchone()[0]
    else:
        return cursor.lastrowid
'''
# --- Nuevas funciones auxiliares para registro de clientes ---

def _obtener_cliente_por_dni(conn, dni):
    """Obtiene un cliente por su DNI. Retorna dict o None."""
    cursor = conn.cursor()
    placeholder = _get_param_placeholder(conn)
    cursor.execute(f'SELECT id, nombre, apellido FROM clientes WHERE dni = {placeholder}', (dni,))
    raw_cliente = cursor.fetchone()
    return _map_row_to_dict(cursor, raw_cliente)

def _obtener_usuario_cliente_por_username(conn, username):
    """Obtiene un usuario_cliente por su username. Retorna dict o None."""
    cursor = conn.cursor()
    placeholder = _get_param_placeholder(conn)
    cursor.execute(f'SELECT id, cliente_id FROM usuarios_clientes WHERE username = {placeholder}', (username,))
    raw_user = cursor.fetchone()
    return _map_row_to_dict(cursor, raw_user)

def _obtener_usuario_cliente_por_cliente_id(conn, cliente_id):
    """Obtiene un usuario_cliente por su cliente_id. Retorna dict o None."""
    print(cliente_id)
    cursor = conn.cursor()
    placeholder = _get_param_placeholder(conn)
    cursor.execute(f'SELECT id, username FROM usuarios_clientes WHERE cliente_id = {placeholder}', (cliente_id,))
    raw_user = cursor.fetchone()
    print(raw_user)
    return _map_row_to_dict(cursor, raw_user)


def registrar_cliente_con_usuario(nombre, apellido, username, password, dni):
    """
    Registra un cliente y su usuario.
    Maneja 3 escenarios:
    1. DNI existente y con usuario: Notifica que ya tiene cuenta.
    2. DNI existente pero sin usuario: Asocia el nuevo usuario al cliente existente.
    3. DNI no existente: Crea un nuevo cliente y un nuevo usuario.   
    """
    conn = obtener_conexion()
    if not conn:
        return False, "Error de conexión a la base de datos."

    try:
        placeholder = _get_param_placeholder(conn)

        # 1. Validar si el DNI ya existe en la tabla de clientes
        cliente_existente_por_dni = dni
        #if dni: # Solo busca por DNI si se proporciona
        cliente_existente_por_dni = _obtener_cliente_por_dni(conn, dni)
        print(cliente_existente_por_dni)
        if cliente_existente_por_dni:
            # Caso A: Cliente encontrado por DNI
            print(f"DEBUG gestor_datos: Cliente existente por DNI: {cliente_existente_por_dni['id']}")
            usuario_existente_para_cliente = _obtener_usuario_cliente_por_cliente_id(conn, cliente_existente_por_dni['id'])
            print("Finalizo hascta aca")
            if usuario_existente_para_cliente:
                # Caso A.1: DNI existe Y ya tiene una cuenta de usuario
                print(f"DEBUG gestor_datos: Usuario ya existente para cliente {cliente_existente_por_dni['id']}.")
                return False, "Ya existe una cuenta asociada a este DNI. Por favor, inicia sesión."
            
            
            else:
                # Caso A.2: DNI existe PERO no tiene cuenta de usuario (lo creó un mecánico)
                # Verificar si el username propuesto ya está en uso por otra cuenta
                if _obtener_usuario_cliente_por_username(conn, username):
                    print(f"DEBUG gestor_datos: El username '{username}' ya está en uso.")
                    return False, "El nombre de usuario propuesto ya está en uso."

                # Crear el usuario y vincularlo al cliente existente
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor = conn.cursor()
                cursor.execute(f'''
                    INSERT INTO usuarios_clientes (cliente_id, username, password)
                    VALUES ({placeholder}, {placeholder}, {placeholder})
                ''', (cliente_existente_por_dni['id'], username, hashed_password))
                conn.commit()
                print(f"DEBUG gestor_datos: Usuario '{username}' asociado al cliente existente con DNI: {dni}.")
                return True, "Cuenta creada y asociada a su DNI existente. Ahora puedes iniciar sesión."
        else:
            # Caso B: DNI NO existe (o no se proporcionó), proceder con nuevo registro
            # Primero, verificar si el username ya está en uso
            if _obtener_usuario_cliente_por_username(conn, username):
                print(f"DEBUG gestor_datos: El username '{username}' ya está en uso.")
                return False, "El nombre de usuario ya existe. Por favor, elige otro."

            # Crear un nuevo cliente (y posiblemente el DNI si se proporcionó)
            cursor = conn.cursor()
            insert_cliente_sql = f'''
                INSERT INTO clientes (nombre, apellido, dni)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            '''
            if isinstance(conn, psycopg2.extensions.connection):
                insert_cliente_sql += ' RETURNING id'
            
            # Si el DNI es None, se pasará None a la DB, lo cual es manejado por la tabla.
            cursor.execute(insert_cliente_sql, (nombre, apellido, dni))
            cliente_id = _get_inserted_id(conn, cursor)
            print(f"DEBUG gestor_datos: Nuevo cliente creado con ID: {cliente_id}")

            # Hashear la contraseña
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Insertar el usuario asociado al cliente nuevo
            cursor.execute(f'''
                INSERT INTO usuarios_clientes (cliente_id, username, password)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            ''', (cliente_id, username, hashed_password))

            conn.commit()
            print(f"DEBUG gestor_datos: Cliente y usuario '{username}' registrados con éxito.")
            return True, "Registro exitoso. ¡Bienvenido! Ya puedes iniciar sesión."

    except (sqlite3.IntegrityError, Psycopg2Error) as e:
        conn.rollback()
        # Mensajes de error más específicos basados en la excepción
        if "unique constraint" in str(e).lower():
            if "usuarios_clientes_username_key" in str(e).lower() or "usuarios_clientes.username" in str(e).lower():
                return False, "El nombre de usuario ya está registrado."
            elif "clientes_dni_key" in str(e).lower() or "clientes.dni" in str(e).lower():
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

            # Paso 1: Insertar el mecánico
            query_mecanico = f'''
                INSERT INTO mecanicos (nombre, apellido, telefono, email)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if isinstance(conn, psycopg2.extensions.connection):
                query_mecanico += ' RETURNING id'
            
            cursor.execute(query_mecanico, (nombre, apellido, telefono, email))
            mecanico_id = _get_inserted_id(conn, cursor)

            # Paso 2: Hashear la contraseña
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Paso 3: Insertar las credenciales
            cursor.execute(f'''
                INSERT INTO usuarios_mecanicos (mecanico_id, username, password)
                VALUES ({placeholder}, {placeholder}, {placeholder})
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
            # SELECCIONAR EXPLÍCITAMENTE LAS COLUMNAS NECESARIAS para evitar conflictos con m.*
            # o si sqlite3.Row no las incluye todas correctamente.
            # Cambié m.* por columnas explícitas para mayor robustez.
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
                # El campo 'id' de mecanicos es ahora 'mecanico_id'
                # Renombramos 'mecanico_id' a 'id' para compatibilidad con el resto del código
                # Esto es importante para session['user_id']
                user_record['id'] = user_record['mecanico_id'] 

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
            placeholder = _get_param_placeholder(conn)
            query = f'''
                INSERT INTO vehiculos (cliente_id, patente, marca, modelo, anio, kilometraje_inicial)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if isinstance(conn, psycopg2.extensions.connection):
                query += ' RETURNING id'
            cursor.execute(query, (cliente_id, patente, marca, modelo, anio, kilometraje_inicial))
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
            query = f'''
                INSERT INTO turnos (cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, estado)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if isinstance(conn, psycopg2.extensions.connection):
                query += ' RETURNING id'
            cursor.execute(query, (cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, 'Agendado'))
            conn.commit()
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
                JOIN vehiculos v ON t.cliente_id = v.cliente_id -- Corregido: t.vehiculo_id = v.id
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
            query = f'''
                INSERT INTO reparaciones (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, estado, turno_origen_id)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            '''
            if isinstance(conn, psycopg2.extensions.connection):
                query += ' RETURNING id'
            cursor.execute(query, (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, 'En Progreso', turno_origen_id))
            reparacion_id = _get_inserted_id(conn, cursor)
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

def obtener_vehiculos_en_taller(): # Nombre de función: obtener_vehiculos_en_taller (ESPAÑOL)
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
            vehiculos_en_taller = [dict(row) for row in raw_data]
        except sqlite3.Error as e:
            print(f"Error al obtener vehículos en taller: {e}")
        finally:
            if conn:
                conn.close()
    return vehiculos_en_taller

# Función para crear una reparación a partir de un turno
def crear_reparacion_desde_turno(turno_id): # Nombre de función: crear_reparacion_desde_turno (ESPAÑOL)
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Obtener los datos del turno
            turno = obtener_turno_por_id(turno_id) 
            if not turno:
                print(f"Turno con ID {turno_id} no encontrado para crear reparación.")
                return None

            # Verificar si ya existe una reparación para este turno para evitar duplicados
            cursor.execute('SELECT id FROM reparaciones WHERE turno_origen_id = ?', (turno_id,))
            existing_reparacion = cursor.fetchone()
            if existing_reparacion:
                print(f"Advertencia: Ya existe una reparación (ID: {existing_reparacion['id']}) para el turno {turno_id}.")
                return existing_reparacion['id']

            # Insertar la nueva reparación
            vehiculo = obtener_vehiculo_por_id(turno['vehiculo_id']) 
            kilometraje_ingreso_reparacion = vehiculo['kilometraje_inicial'] if vehiculo else 0

            cursor.execute('''
                INSERT INTO reparaciones (vehiculo_id, mecanico_id, fecha_ingreso, kilometraje_ingreso, problema_reportado, estado, turno_origen_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (turno['vehiculo_id'], turno['mecanico_id'], turno['fecha'], # Usar fecha del turno como fecha_ingreso de la reparación
                  kilometraje_ingreso_reparacion, 
                  turno['problema_reportado'], 'En Progreso', turno_id)) # Estado inicial de la reparación 'En Progreso'
            
            reparacion_id = cursor.lastrowid

            # *** CAMBIO AQUÍ: Actualizar el estado del turno a 'Completado' ***
            # Esto lo saca de la lista de turnos activos, pero mantiene el registro.
            cursor.execute('UPDATE turnos SET estado = ? WHERE id = ?', ('Completado', turno_id))
            
            conn.commit()
            return reparacion_id
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: reparaciones.turno_origen_id" in str(e):
                print(f"Error: Intento de crear reparación duplicada para turno {turno_id}. Ya existe.")
            else:
                print(f"Error de integridad al agregar reparación desde turno {turno_id}: {e}")
            return None
        except sqlite3.Error as e:
            print(f"Error al crear reparación desde turno {turno_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()
    return None

# Puedes añadir un bloque para pruebas manuales si lo necesitas
if __name__ == '__main__':
    # Para forzar el uso de SQLite para pruebas locales, asegúrate de que DATABASE_URL no esté definida.
    # Si la habías definido manualmente en tu terminal, desconfigúrala antes de ejecutar:
    # PowerShell: Remove-Item Env:\DATABASE_URL
    # Bash/Zsh: unset DATABASE_URL
    
    # Crea las tablas si no existen (usará SQLite localmente)
    crear_tablas()

    # # BLOQUE DE PRUEBAS MANUALES (COMENTADO POR DEFECTO PARA EVITAR CREACIONES DUPLICADAS)
    # try:
    #     print("Intentando agregar mecánico para pruebas...")
    #     # Intenta crear un mecánico si no existe
    #     mecanico_agregado = agregar_mecanico("Beto", "Test", "111222333", "beto@taller.com", "Beto", "asd")
    #     if mecanico_agregado:
    #         print("Mecánico 'Beto' agregado o ya existe.")
    #     else:
    #         print("Fallo al agregar mecánico 'Beto'.")
    # except Exception as e:
    #     print(f"Error durante la prueba de agregar_mecanico: {e}")

    # Luego puedes ejecutar la app Flask
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port, debug=False)
