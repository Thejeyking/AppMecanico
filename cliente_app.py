import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import gestor_datos # Importa el módulo para interactuar con la base de datos

# ==========================================================
# Inicialización de la aplicación Flask para clientes
# ==========================================================
# Configura la aplicación Flask para servir los archivos del frontend de React.
# 'static_folder': donde Flask buscará los archivos JS, CSS, imágenes, etc., de React.
# 'static_url_path': el prefijo URL para acceder a los archivos estáticos (ej. /static/js/main.js).
# 'template_folder': donde Flask buscará el archivo HTML principal de React (generalmente index.html).
cliente_app = Flask(__name__, static_folder='static_cliente', static_url_path='/static', template_folder='templates_cliente')
cliente_app.secret_key = os.environ.get("CLIENT_SECRET_KEY", "una_clave_secreta_muy_larga_y_aleatoria_para_pruebas_locales_FIJA")

# ==========================================================
# Configuración de Base de Datos y Tablas
# ==========================================================
# Este decorador asegura que las tablas de la base de datos se creen
# antes de cada solicitud si no existen.
@cliente_app.before_request
def before_request_create_tables():
    gestor_datos.crear_tablas()

# ==========================================================
# Rutas de la Aplicación (Servir el Frontend)
# ==========================================================
@cliente_app.route('/')
def index_cliente():
    """
    Renderiza la página de inicio para el cliente.
    Esta ruta está diseñada para cargar la aplicación React.
    Flask buscará 'index.html' en la carpeta 'templates_cliente'.
    """
    return render_template('index.html')

# ==========================================================
# API Endpoints (Para la comunicación con la aplicación React)
# ==========================================================
# En cliente_app.py
@cliente_app.route('/api/registro', methods=['POST'])
def registro_api():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    nombre_cliente = data.get('nombre_cliente')
    apellido_cliente = data.get('apellido_cliente')
    dni_cliente = data.get('dni_cliente') 

    if not username or not password or not nombre_cliente or not apellido_cliente:
        return jsonify({'success': False, 'message': 'Faltan datos requeridos (usuario, contraseña, nombre, apellido, dni).'}), 400

    success, message = gestor_datos.registrar_cliente_con_usuario(
        nombre=nombre_cliente,
        apellido=apellido_cliente,
        username=username,
        password=password,
        dni=dni_cliente
    )

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        # El mensaje de error ahora será más específico desde gestor_datos.
        # Puedes mantener el status_code general o ajustarlo según los mensajes específicos si lo necesitas en el frontend.
        status_code = 409 if "ya existe" in message or "ya está registrado" in message else 400
        return jsonify({'success': False, 'message': message}), status_code

@cliente_app.route('/api/login', methods=['POST'])
def login_api():
    """
    Endpoint para el inicio de sesión de clientes.
    Verifica las credenciales y establece la sesión del cliente.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Faltan usuario o contraseña.'}), 400

    # Llama a la función del gestor de datos para verificar las credenciales.
    usuario_cliente_data = gestor_datos.verificar_credenciales_cliente(username, password)

    if usuario_cliente_data:
        # Si las credenciales son válidas, guarda la información del cliente en la sesión.
        session['cliente_user_id'] = usuario_cliente_data['usuario_cliente_id']
        session['cliente_id'] = usuario_cliente_data['cliente_id']
        session['username'] = usuario_cliente_data['username']
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso.', 'cliente_id': usuario_cliente_data['cliente_id']})
    else:
        return jsonify({'success': False, 'message': 'Credenciales inválidas.'}), 401

@cliente_app.route('/api/logout')
def logout_api():
    """
    Endpoint para cerrar la sesión del cliente.
    Elimina la información de la sesión.
    """
    session.pop('cliente_user_id', None)
    session.pop('cliente_id', None)
    session.pop('username', None)
    return jsonify({'success': True, 'message': 'Sesión cerrada.'})

@cliente_app.route('/api/check_session')
def check_session():
    """
    Endpoint para verificar el estado de la sesión del cliente.
    Útil para que el frontend sepa si el usuario está logueado.
    """
    if 'cliente_id' in session and 'username' in session:
        return jsonify({'logged_in': True, 'cliente_id': session['cliente_id'], 'username': session['username']})
    return jsonify({'logged_in': False})

@cliente_app.route('/api/cliente/dashboard')
def cliente_dashboard_api():
    """
    Endpoint para obtener los datos del dashboard del cliente.
    Requiere autenticación.
    """
    if 'cliente_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    cliente_id = session['cliente_id']
    cliente = gestor_datos.obtener_cliente_por_id(cliente_id)
    vehiculos = gestor_datos.obtener_vehiculos_por_cliente(cliente_id)

    if cliente:
        # Convierte los objetos de fila de la base de datos a diccionarios.
        vehiculos_dict = [dict(v) for v in vehiculos]
        return jsonify({'success': True, 'cliente': dict(cliente), 'vehiculos': vehiculos_dict})
    return jsonify({'success': False, 'message': 'Cliente no encontrado.'}), 404

@cliente_app.route('/api/vehiculo/<int:vehiculo_id>/historial')
def vehiculo_historial_api(vehiculo_id):
    """
    Endpoint para obtener el historial de reparaciones de un vehículo específico.
    Requiere autenticación y que el vehículo pertenezca al cliente logueado.
    """
    if 'cliente_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    # Obtiene el historial de reparaciones del gestor de datos.
    historial = gestor_datos.obtener_historial_reparaciones_vehiculo(vehiculo_id)

    # Verifica que el vehículo pertenezca al cliente actual por seguridad.
    vehiculo_info = gestor_datos.obtener_vehiculo_por_id(vehiculo_id)
    if not vehiculo_info or vehiculo_info['cliente_id'] != session['cliente_id']:
        return jsonify({'success': False, 'message': 'Acceso denegado a este vehículo o historial no encontrado.'}), 403

    return jsonify({'success': True, 'historial': [dict(h) for h in historial]})

@cliente_app.route('/api/vehiculo/<int:vehiculo_id>/estado_activo')
def vehiculo_estado_activo_api(vehiculo_id):
    """
    Endpoint para obtener el estado de la reparación activa de un vehículo.
    Útil para mostrar el progreso de un vehículo en el taller.
    """
    if 'cliente_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    # Verifica que el vehículo pertenezca al cliente actual por seguridad.
    vehiculo_info = gestor_datos.obtener_vehiculo_por_id(vehiculo_id)
    if not vehiculo_info or vehiculo_info['cliente_id'] != session['cliente_id']:
        return jsonify({'success': False, 'message': 'Acceso denegado a este vehículo o reparación no encontrada.'}), 403

    # Obtiene la reparación activa del vehículo.
    reparacion_activa = gestor_datos.obtener_reparacion_activa_por_vehiculo(vehiculo_id)

    if reparacion_activa:
        return jsonify({'success': True, 'reparacion': dict(reparacion_activa)})
    return jsonify({'success': False, 'message': 'No hay reparación activa para este vehículo.'})

# ==========================================================
# Punto de Arranque de la Aplicación Flask (Ajustado para Despliegue Web)
# ==========================================================
if __name__ == '__main__':
    # Crea las tablas de la base de datos si no existen.
    # Esto es importante para el primer arranque, especialmente en entornos de despliegue.
    gestor_datos.crear_tablas()

    # Obtiene el puerto de la variable de entorno 'PORT' (común en plataformas como Render).
    # Si no está definida (ej. desarrollo local), usa el puerto 5001 por defecto para el cliente.
    # Asegúrate de usar un puerto diferente para cada app si las ejecutas localmente al mismo tiempo.
    port = int(os.environ.get("PORT", 5001))

    # Ejecuta la aplicación Flask en todas las interfaces (0.0.0.0) y el puerto proporcionado.
    # debug=False es CRÍTICO para producción por razones de seguridad y rendimiento.
    cliente_app.run(host="0.0.0.0", port=port, debug=False)
