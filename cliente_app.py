import os
import bcrypt 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import gestor_datos 
import threading # NUEVO: Para ejecutar Flask en un hilo separado
import webview # NUEVO: Para crear la ventana de escritorio
import time # NUEVO: Para dar tiempo al servidor Flask a iniciar

# Inicialización de la aplicación Flask para clientes
cliente_app = Flask(__name__, static_folder='static_cliente', static_url_path='/static', template_folder='templates_cliente')
cliente_app.secret_key = os.urandom(24).hex() 

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
    print(f"DEBUG_API: Datos JSON recibidos para registro: {data}")
    
    username = data.get('username')
    password = data.get('password')
    nombre_cliente = data.get('nombre_cliente')
    apellido_cliente = data.get('apellido_cliente')
    
    dni = data.get('dni')
    
    print(f"DEBUG_API: Valores extraídos para registro - Username: {username}, Nombre: {nombre_cliente}, Apellido: {apellido_cliente}, DNI: {dni}")

    if not username or not password or not nombre_cliente or not apellido_cliente:
        print("DEBUG_API: Faltan datos requeridos (usuario, contraseña, nombre, apellido) para el registro.")
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
        print(f"DEBUG_API: Fallo en el registro: {message}, Código de estado: {status_code}")
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
# PUNTO DE ARRANQUE DE LA APLICACIÓN FLASK (MODIFICADO PARA ESCRITORIO)
# ==========================================================
def start_cliente_app():
    gestor_datos.crear_tablas()
    cliente_app.run(debug=False, host='127.0.0.1', port=5001)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_cliente_app)
    flask_thread.daemon = True 
    flask_thread.start()

    time.sleep(2) 

    webview.create_window('Taller Mecánico (Cliente)', 'http://127.0.0.1:5001', width=1000, height=700)
    webview.start()

