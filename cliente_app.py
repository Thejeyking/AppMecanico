import os
import bcrypt 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import gestor_datos 
# No se necesitan 'threading', 'webview', 'time' para el despliegue web

# Inicialización de la aplicación Flask para clientes
cliente_app = Flask(__name__, static_folder='static_cliente', static_url_path='/static', template_folder='templates_cliente')
cliente_app.secret_key = os.urandom(24).hex() # Clave secreta para sesiones seguras

# ==========================================================
# CONFIGURACIÓN DE BASE DE DATOS Y TABLAS
# ==========================================================
@cliente_app.before_request
def before_request_create_tables():
    gestor_datos.crear_tablas()

# ==========================================================
# RUTAS DE LA APLICACIÓN
# ==========================================================
@cliente_app.route('/')
def index_cliente():
    """Renderiza la página de inicio para el cliente, que cargará la aplicación React."""
    return render_template('index.html')

# ==========================================================
# API ENDPOINTS
# ==========================================================
@cliente_app.route('/api/registro', methods=['POST'])
def registro_api():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    nombre_cliente = data.get('nombre_cliente')
    apellido_cliente = data.get('apellido_cliente')
    
    dni = data.get('dni')
    
    if not username or not password or not nombre_cliente or not apellido_cliente:
        return jsonify({'success': False, 'message': 'Faltan datos requeridos (usuario, contraseña, nombre, apellido).'}), 400

    success, message = gestor_datos.registrar_cliente_con_usuario(
        nombre=nombre_cliente,
        apellido=apellido_cliente,
        username=username,
        password=password,
        dni=dni
    )

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        status_code = 409 if "ya existe" in message else 400
        return jsonify({'success': False, 'message': message}), status_code
    
@cliente_app.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Faltan usuario o contraseña.'}), 400

    usuario_cliente_data = gestor_datos.verificar_credenciales_cliente(username, password)

    if usuario_cliente_data:
        session['cliente_user_id'] = usuario_cliente_data['usuario_cliente_id']
        session['cliente_id'] = usuario_cliente_data['cliente_id']
        session['username'] = usuario_cliente_data['username']
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso.', 'cliente_id': usuario_cliente_data['cliente_id']})
    else:
        return jsonify({'success': False, 'message': 'Credenciales inválidas.'}), 401

@cliente_app.route('/api/logout')
def logout_api():
    session.pop('cliente_user_id', None)
    session.pop('cliente_id', None)
    session.pop('username', None)
    return jsonify({'success': True, 'message': 'Sesión cerrada.'})

@cliente_app.route('/api/check_session')
def check_session():
    if 'cliente_id' in session and 'username' in session:
        return jsonify({'logged_in': True, 'cliente_id': session['cliente_id'], 'username': session['username']})
    return jsonify({'logged_in': False})

@cliente_app.route('/api/cliente/dashboard')
def cliente_dashboard_api():
    if 'cliente_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    cliente_id = session['cliente_id']
    cliente = gestor_datos.obtener_cliente_por_id(cliente_id) 
    vehiculos = gestor_datos.obtener_vehiculos_por_cliente(cliente_id)

    if cliente:
        vehiculos_dict = [dict(v) for v in vehiculos] 
        return jsonify({'success': True, 'cliente': dict(cliente), 'vehiculos': vehiculos_dict})
    return jsonify({'success': False, 'message': 'Cliente no encontrado.'}), 404

@cliente_app.route('/api/vehiculo/<int:vehiculo_id>/historial')
def vehiculo_historial_api(vehiculo_id):
    if 'cliente_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    historial = gestor_datos.obtener_historial_reparaciones_vehiculo(vehiculo_id)
    
    vehiculo_info = gestor_datos.obtener_vehiculo_por_id(vehiculo_id)
    if not vehiculo_info or vehiculo_info['cliente_id'] != session['cliente_id']:
        return jsonify({'success': False, 'message': 'Acceso denegado a este vehículo o historial no encontrado.'}), 403

    return jsonify({'success': True, 'historial': [dict(h) for h in historial]})

@cliente_app.route('/api/vehiculo/<int:vehiculo_id>/estado_activo')
def vehiculo_estado_activo_api(vehiculo_id):
    if 'cliente_id' not in session:
        return jsonify({'success': False, 'message': 'No autenticado.'}), 401

    vehiculo_info = gestor_datos.obtener_vehiculo_por_id(vehiculo_id)
    if not vehiculo_info or vehiculo_info['cliente_id'] != session['cliente_id']:
        return jsonify({'success': False, 'message': 'Acceso denegado a este vehículo o reparación no encontrada.'}), 403

    reparacion_activa = gestor_datos.obtener_reparacion_activa_por_vehiculo(vehiculo_id)
    
    if reparacion_activa:
        return jsonify({'success': True, 'reparacion': dict(reparacion_activa)})
    return jsonify({'success': False, 'message': 'No hay reparación activa para este vehículo.'})

# ==========================================================
# PUNTO DE ARRANQUE DE LA APLICACIÓN FLASK (PARA DESPLIEGUE WEB)
# ==========================================================
if __name__ == '__main__':
    gestor_datos.crear_tablas() # Las tablas se crearán en la base de datos de Render la primera vez
    # En un entorno de producción, Render/Gunicorn/Waitress usará esto para iniciar la aplicación.
    # No especifiques host/port aquí, Render lo gestiona.
    cliente_app.run(debug=False)

