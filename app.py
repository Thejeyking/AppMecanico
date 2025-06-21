import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import gestor_datos
from datetime import date, datetime # Se importa aquí para usarlo en detalle_reparacion

# ==========================================================
# CONFIGURACIÓN DE LA APLICACIÓN FLASK
# ==========================================================
app = Flask(__name__)
# ¡IMPORTANTE para desarrollo local!
# Para producción, esta clave DEBE obtenerse de una variable de entorno.
# Para pruebas locales, puedes usar una cadena fuerte directamente aquí,
# o seguir usando os.environ.get para flexibilidad si ya tienes la variable configurada.
# Si la ejecutas localmente sin la variable de entorno 'SECRET_KEY', usará el valor por defecto.
app.secret_key = os.environ.get("SECRET_KEY", "una_clave_secreta_muy_larga_y_aleatoria_para_pruebas_locales")

# ==========================================================
# 1. DECORADOR PARA REQUERIR INICIO DE SESIÓN
# ==========================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('rol') != 'mecanico':
            flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login_mecanico'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================================
# 2. CONFIGURACIÓN DE BASE DE DATOS Y TABLAS (al inicio de la aplicación)
# ==========================================================
@app.before_request
def before_request():
    gestor_datos.crear_tablas()


# ==========================================================
# 3. RUTAS DE AUTENTICACIÓN (Login y Logout)
# ==========================================================
@app.route('/login', methods=['GET', 'POST'])
def login_mecanico():
    if 'username' in session and session.get('rol') == 'mecanico':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mecanico = gestor_datos.verificar_credenciales_mecanico(username, password)
        if mecanico:
            session['username'] = username
            session['user_id'] = mecanico['id']
            session['rol'] = 'mecanico'
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required 
def logout_mecanico():
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('rol', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login_mecanico'))


# ==========================================================
# 4. RUTAS PRINCIPALES PROTEGIDAS
# ==========================================================

@app.route('/')
@app.route('/dashboard')
@login_required 
def dashboard():
    return render_template('dashboard.html')


@app.route('/clientes')
@login_required 
def clientes():
    clientes = gestor_datos.obtener_todos_los_clientes()
    return render_template('clientes.html', clientes=clientes)


@app.route('/clientes/agregar', methods=['GET', 'POST'])
@login_required 
def agregar_cliente_web():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']
        dni = request.form['dni']
        
        if gestor_datos.agregar_cliente(nombre, apellido, telefono, email, dni):
            flash('Cliente agregado exitosamente.', 'success')
            return redirect(url_for('clientes'))
        else:
            flash('Error al agregar cliente. El DNI podría ya existir.', 'error')
    return render_template('cliente_form.html', accion='Agregar Cliente')


@app.route('/clientes/modificar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required 
def modificar_cliente_web(cliente_id):
    cliente = gestor_datos.obtener_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente no encontrado.', 'error')
        return redirect(url_for('clientes'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']
        dni = request.form['dni']

        if gestor_datos.actualizar_cliente(cliente_id, nombre, apellido, telefono, email, dni):
            flash('Cliente actualizado exitosamente.', 'success')
            return redirect(url_for('clientes'))
        else:
            flash('Error al actualizar cliente. El DNI podría ya existir.', 'error')
    return render_template('cliente_form.html', cliente=cliente, accion='Modificar Cliente')


@app.route('/clientes/eliminar/<int:cliente_id>', methods=['POST'])
@login_required 
def eliminar_cliente_web(cliente_id):
    if gestor_datos.eliminar_cliente(cliente_id):
        flash('Cliente y sus vehículos asociados eliminados exitosamente.', 'success')
    else:
        flash('Error al eliminar cliente.', 'error')
    return redirect(url_for('clientes'))


@app.route('/clientes/<int:cliente_id>')
@login_required 
def detalle_cliente(cliente_id):
    cliente = gestor_datos.obtener_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente no encontrado.', 'error')
        return redirect(url_for('clientes'))
    
    vehiculos = gestor_datos.obtener_vehiculos_por_cliente(cliente_id)
    
    return render_template('detalle_cliente.html', cliente=cliente, vehiculos=vehiculos)


# ==========================================================
# 5. RUTAS DE VEHÍCULOS PROTEGIDAS
# ==========================================================

@app.route('/vehiculo/agregar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required 
def agregar_vehiculo_web(cliente_id):
    cliente = gestor_datos.obtener_cliente_por_id(cliente_id)
    if not cliente:
        flash('Cliente no encontrado.', 'error')
        return redirect(url_for('clientes'))

    if request.method == 'POST':
        patente = request.form['patente']
        marca = request.form['marca']
        modelo = request.form['modelo']
        anio = request.form['anio']
        kilometraje_inicial = request.form['kilometraje_inicial']
        
        if gestor_datos.agregar_vehiculo(cliente_id, patente, marca, modelo, anio, kilometraje_inicial):
            flash('Vehículo agregado exitosamente.', 'success')
            return redirect(url_for('detalle_cliente', cliente_id=cliente_id))
        else:
            flash('Error al agregar vehículo. La patente podría ya existir.', 'error')
    
    return render_template('vehiculo_form.html', cliente=cliente, accion='Agregar Vehículo')


@app.route('/vehiculo/modificar/<int:vehiculo_id>', methods=['GET', 'POST'])
@login_required 
def modificar_vehiculo(vehiculo_id):
    vehiculo = gestor_datos.obtener_vehiculo_por_id(vehiculo_id)
    if not vehiculo:
        flash('Vehículo no encontrado.', 'error')
        return redirect(url_for('clientes'))

    if request.method == 'POST':
        marca = request.form['marca']
        modelo = request.form['modelo']
        anio = request.form['anio']
        patente = request.form['patente']
        kilometraje_inicial = request.form['kilometraje_inicial']

        if gestor_datos.actualizar_vehiculo(vehiculo_id, marca, modelo, anio, patente, kilometraje_inicial):
            flash('Vehículo actualizado exitosamente.', 'success')
            return redirect(url_for('detalle_cliente', cliente_id=vehiculo['cliente_id']))
        else:
            flash('Error al actualizar el vehículo.', 'error')
    
    return render_template('vehiculo_form.html', vehiculo=vehiculo, accion='Modificar Vehículo')


@app.route('/vehiculo/eliminar/<int:vehiculo_id>', methods=['POST'])
@login_required 
def eliminar_vehiculo_web(vehiculo_id):
    vehiculo_info = gestor_datos.obtener_vehiculo_por_id(vehiculo_id)
    
    if gestor_datos.eliminar_vehiculo(vehiculo_id):
        flash('Vehículo eliminado exitosamente.', 'success')
        if vehiculo_info and vehiculo_info['cliente_id']:
            return redirect(url_for('detalle_cliente', cliente_id=vehiculo_info['cliente_id']))
        else:
            return redirect(url_for('clientes'))
    else:
        flash('Error al eliminar el vehículo.', 'error')
        if vehiculo_info and vehiculo_info['cliente_id']:
            return redirect(url_for('detalle_cliente', cliente_id=vehiculo_info['cliente_id']))
        else:
            return redirect(url_for('clientes'))


@app.route('/vehiculo/<int:vehiculo_id>/historial', methods=['GET'])
@login_required
def historial_vehiculo(vehiculo_id):
    """Muestra el historial de reparaciones para un vehículo específico."""
    print(f"\nDEBUG FLASK (app.py): === INICIO DE RUTA historial_vehiculo para ID: {vehiculo_id} ===")
    
    vehiculo = gestor_datos.obtener_vehiculo_por_id(vehiculo_id)
    if not vehiculo:
        flash('Vehículo no encontrado.', 'error')
        print(f"DEBUG FLASK (app.py): Vehículo con ID {vehiculo_id} NO encontrado. Redirigiendo a clientes.")
        return redirect(url_for('clientes'))
        
    historial = gestor_datos.obtener_historial_reparaciones_vehiculo(vehiculo_id)
    
    # Añadir datos de cliente al vehículo para el template si no vienen con la consulta de historial
    if 'nombre_cliente' not in vehiculo:
        cliente_del_vehiculo = gestor_datos.obtener_cliente_por_id(vehiculo['cliente_id'])
        if cliente_del_vehiculo:
            vehiculo['nombre_cliente'] = cliente_del_vehiculo['nombre']
            vehiculo['apellido_cliente'] = cliente_del_vehiculo['apellido']
            vehiculo['dni_cliente'] = cliente_del_vehiculo['dni'] # Añadir DNI para el template
        else:
            vehiculo['nombre_cliente'] = 'N/A'
            vehiculo['apellido_cliente'] = 'N/A'
            vehiculo['dni_cliente'] = 'N/A'


    print(f"DEBUG FLASK (app.py): Vehículo recuperado para historial: {vehiculo}")
    print(f"DEBUG FLASK (app.py): Historial de reparaciones recuperado: {historial}")
    print(f"DEBUG FLASK (app.py): === FIN DE RUTA historial_vehiculo ===\n")
    return render_template('historial_vehiculo.html', vehiculo=vehiculo, historial=historial)


# ==========================================================
# 6. RUTAS DE MECÁNICOS PROTEGIDAS
# ==========================================================

@app.route('/mecanicos')
@login_required 
def mecanicos():
    mecanicos = gestor_datos.obtener_todos_los_mecanicos()
    return render_template('mecanicos.html', mecanicos=mecanicos)

@app.route('/mecanicos/agregar', methods=['GET', 'POST'])
@login_required 
def agregar_mecanico_web():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if gestor_datos.agregar_mecanico(nombre, apellido, telefono, email, username, password):
            flash('Mecánico agregado exitosamente.', 'success')
            return redirect(url_for('mecanicos'))
        else:
            flash('Error al agregar mecánico. El nombre de usuario podría ya existir.', 'error')
    return render_template('mecanico_form.html', accion='Agregar Mecánico')

@app.route('/mecanicos/modificar/<int:mecanico_id>', methods=['GET', 'POST'])
@login_required 
def modificar_mecanico_web(mecanico_id):
    mecanico = gestor_datos.obtener_mecanico_por_id(mecanico_id)
    if not mecanico:
        flash('Mecánico no encontrado.', 'error')
        return redirect(url_for('mecanicos'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']
        
        if gestor_datos.actualizar_mecanico(mecanico_id, nombre, apellido, telefono, email):
            flash('Mecánico actualizado exitosamente.', 'success')
            return redirect(url_for('mecanicos'))
        else:
            flash('Error al actualizar el mecánico.', 'error')
    return render_template('mecanico_form.html', mecanico=mecanico, accion='Modificar Mecánico')


@app.route('/mecanicos/eliminar/<int:mecanico_id>', methods=['POST'])
@login_required 
def eliminar_mecanico_web(mecanico_id):
    if gestor_datos.eliminar_mecanico(mecanico_id):
        flash('Mecánico eliminado exitosamente.', 'success')
    else:
        flash('Error al eliminar el mecánico.', 'error')
    return redirect(url_for('mecanicos'))


# ==========================================================
# 7. RUTAS DE TURNOS PROTEGIDAS
# ==========================================================

@app.route('/turnos')
@login_required 
def lista_turnos():
    turnos = gestor_datos.obtener_todos_los_turnos() 
    return render_template('turnos.html', turnos=turnos)



@app.route('/turnos/agregar', methods=['GET', 'POST'])
@login_required 
def agregar_turno_web():
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        vehiculo_id = request.form['vehiculo_id']
        mecanico_id = request.form['mecanico_id']
        fecha = request.form['fecha']
        hora = request.form['hora'] 
        problema_reportado = request.form['problema_reportado']

        if gestor_datos.agregar_turno(cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado):
            flash('Turno agendado exitosamente.', 'success')
            return redirect(url_for('lista_turnos'))
        else:
            flash('Error al agendar el turno.', 'error')
    
    clientes = gestor_datos.obtener_todos_los_clientes()
    mecanicos = gestor_datos.obtener_todos_los_mecanicos()
    return render_template('agendar_turno.html', clientes=clientes, mecanicos=mecanicos, accion='Agendar Nuevo Turno')


@app.route('/turnos/modificar/<int:turno_id>', methods=['GET', 'POST'])
@login_required 
def modificar_turno_web(turno_id):
    turno = gestor_datos.obtener_turno_por_id(turno_id) 
    if not turno:
        flash('Turno no encontrado.', 'error')
        return redirect(url_for('lista_turnos'))

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        vehiculo_id = request.form['vehiculo_id']
        mecanico_id = request.form['mecanico_id']
        fecha = request.form['fecha']
        hora = request.form['hora']
        problema_reportado = request.form['problema_reportado']
        estado = request.form['estado']

        if gestor_datos.actualizar_turno(turno_id, cliente_id, vehiculo_id, mecanico_id, fecha, hora, problema_reportado, estado):
            # Si el turno pasa a "En Progreso", intentar crear una reparación si no existe
            if estado == 'En Progreso':
                reparacion_id = gestor_datos.crear_reparacion_desde_turno(turno_id)
                if reparacion_id:
                    flash('Reparación iniciada desde el turno.', 'info')
                else:
                    flash('Advertencia: No se pudo iniciar la reparación desde el turno o ya existía.', 'warning')
            flash('Turno actualizado exitosamente.', 'success')
            return redirect(url_for('lista_turnos'))
        else:
            flash('Error al actualizar el turno.', 'error')
    
    clientes = gestor_datos.obtener_todos_los_clientes()
    mecanicos = gestor_datos.obtener_todos_los_mecanicos()
    vehiculos = []
    if turno and turno['cliente_id']: # Asegurarse de que turno y cliente_id existan
        vehiculos = gestor_datos.obtener_vehiculos_por_cliente(turno['cliente_id'])

    return render_template('agendar_turno.html', turno=turno, clientes=clientes, mecanicos=mecanicos, vehiculos=vehiculos, accion='Modificar Turno')


@app.route('/turnos/eliminar/<int:turno_id>', methods=['POST'])
@login_required 
def eliminar_turno_web(turno_id):
    if gestor_datos.eliminar_turno(turno_id): 
        flash('Turno eliminado exitosamente.', 'success')
    else:
        flash('Error al eliminar el turno.', 'error')
    return redirect(url_for('lista_turnos'))


@app.route('/turnos/pasar_a_taller/<int:turno_id>', methods=['POST'])
@login_required
def pasar_turno_a_taller(turno_id):
    mecanico_id_sesion = session.get('user_id')
    if not mecanico_id_sesion:
        flash("Error: Mecánico no identificado en la sesión.", 'error')
        return redirect(url_for('lista_turnos'))

    turno = gestor_datos.obtener_turno_por_id(turno_id)
    if not turno:
        flash('Turno no encontrado.', 'error')
        return redirect(url_for('lista_turnos'))

    if turno['estado'] in ['Completado', 'En Progreso', 'Cancelado']:
        flash(f'El turno ya está en estado "{turno["estado"]}". No se puede pasar a taller.', 'warning')
        return redirect(url_for('lista_turnos'))
    
    reparacion_id = gestor_datos.crear_reparacion_desde_turno(turno_id)
    
    if reparacion_id:
        flash(f'Turno {turno_id} pasado a taller como Reparación ID: {reparacion_id}.', 'success')
        return redirect(url_for('vehiculos_en_taller'))
    else:
        flash('Error al pasar el turno a taller. Puede que ya exista una reparación para este turno.', 'error')
        return redirect(url_for('lista_turnos'))


# ==========================================================
# 8. RUTAS DE REPARACIONES PROTEGIDAS
# ==========================================================

@app.route('/reparaciones/ingreso_directo', methods=['GET', 'POST'])
@login_required
def registrar_ingreso_directo():
    mecanico_id_sesion = session.get('user_id')

    if request.method == 'POST':
        vehiculo_id = request.form['vehiculo_id']
        fecha_ingreso = request.form['fecha_ingreso']
        kilometraje_ingreso = request.form['kilometraje_ingreso']
        problema_reportado = request.form['problema_reportado']

        reparacion_id = gestor_datos.agregar_reparacion(
            vehiculo_id,
            mecanico_id_sesion,
            fecha_ingreso,
            kilometraje_ingreso,
            problema_reportado
        )
        if reparacion_id:
            flash(f'Ingreso directo registrado como Reparación ID: {reparacion_id}.', 'success')
            return redirect(url_for('vehiculos_en_taller'))
        else:
            flash('Error al registrar el ingreso directo.', 'error')
    
    clientes = gestor_datos.obtener_todos_los_clientes()
    vehiculos = [] 
    for cliente in clientes:
        vehiculos.extend(gestor_datos.obtener_vehiculos_por_cliente(cliente['id']))

    return render_template('reparacion_directa_form.html', clientes=clientes, vehiculos=vehiculos)


@app.route('/reparaciones/detalle/<int:reparacion_id>', methods=['GET'])
@login_required
def detalle_reparacion(reparacion_id):
    reparacion = gestor_datos.obtener_reparacion_por_id(reparacion_id)
    if not reparacion:
        flash('Reparación no encontrada.', 'error')
        return redirect(url_for('vehiculos_en_taller'))
    
    if reparacion['fecha_salida']:
        try:
            reparacion['fecha_salida_formato'] = datetime.strptime(reparacion['fecha_salida'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except ValueError:
            reparacion['fecha_salida_formato'] = reparacion['fecha_salida']
    else:
        reparacion['fecha_salida_formato'] = 'N/A'

    return render_template('detalle_reparacion.html', reparacion=reparacion)


@app.route('/reparaciones/registrar_directa', methods=['GET', 'POST'])
@login_required
def registrar_reparacion_directa_web():
    """
    Permite registrar una nueva reparación directamente en el taller.
    No vinculada a un turno previo.
    """
    print(f"DEBUG FLASK: Accediendo a registrar_reparacion_directa_web. Sesión: {session.get('username')}")
    if request.method == 'POST':
        vehiculo_id = request.form['vehiculo_id']
        mecanico_id = request.form['mecanico_id'] if request.form['mecanico_id'] else None
        fecha_ingreso = request.form['fecha_ingreso']
        kilometraje_ingreso = request.form['kilometraje_ingreso']
        problema_reportado = request.form['problema_reportado']

        reparacion_id = gestor_datos.agregar_reparacion(
            vehiculo_id, mecanico_id, fecha_ingreso,
            kilometraje_ingreso, problema_reportado
        )
        
        if reparacion_id:
            flash('Reparación registrada exitosamente.', 'success')
            return redirect(url_for('detalle_reparacion_web', reparacion_id=reparacion_id))
        else:
            flash('Error al registrar la reparación.', 'error')
    
    clientes = gestor_datos.obtener_todos_los_clientes()
    mecanicos = gestor_datos.obtener_todos_los_mecanicos()
    today_date = date.today().isoformat() # Formato YYYY-MM-DD
    return render_template('ingreso_taller_form.html', clientes=clientes, mecanicos=mecanicos, today_date=today_date)


@app.route('/reparaciones/<int:reparacion_id>', methods=['GET'])
@login_required
def detalle_reparacion_web(reparacion_id):
    """Muestra los detalles de una reparación específica."""
    print(f"DEBUG FLASK: Accediendo a detalle_reparacion_web para ID: {reparacion_id}. Sesión: {session.get('username')}")
    reparacion = gestor_datos.obtener_reparacion_por_id(reparacion_id)
    if not reparacion:
        flash('Reparación no encontrada.', 'error')
        return redirect(url_for('en_taller')) # Redirigir a "En Taller" o dashboard

    return render_template('reparacion_detalle.html', reparacion=reparacion)

@app.route('/reparaciones/modificar/<int:reparacion_id>', methods=['GET', 'POST'])
@login_required
def modificar_reparacion_web(reparacion_id):
    """
    Permite modificar los detalles de una reparación existente.
    Esto podría incluir cambiar estado, trabajos, repuestos, costos, etc.
    """
    print(f"DEBUG FLASK: Accediendo a modificar_reparacion_web para ID: {reparacion_id}. Sesión: {session.get('username')}")
    reparacion = gestor_datos.obtener_reparacion_por_id(reparacion_id)
    if not reparacion:
        flash('Reparación no encontrada.', 'error')
        return redirect(url_for('en_taller'))

    if request.method == 'POST':
        estado = request.form.get('estado')
        trabajos_realizados = request.form.get('trabajos_realizados')
        repuestos_usados = request.form.get('repuestos_usados')
        costo_mano_obra = float(request.form.get('costo_mano_obra') or 0.0)
        costo_total = float(request.form.get('costo_total') or 0.0)
        fecha_salida = request.form.get('fecha_salida') if request.form.get('fecha_salida') else None
        kilometraje_salida = int(request.form.get('kilometraje_salida') or 0) if request.form.get('kilometraje_salida') else None

        if gestor_datos.actualizar_estado_reparacion(
            reparacion_id, estado, trabajos_realizados, repuestos_usados,
            costo_mano_obra, costo_total, fecha_salida, kilometraje_salida
        ):
            flash('Reparación actualizada exitosamente.', 'success')
            return redirect(url_for('detalle_reparacion_web', reparacion_id=reparacion_id))
        else:
            flash('Error al actualizar la reparación.', 'error')
        
    mecanicos = gestor_datos.obtener_todos_los_mecanicos()
    return render_template('modificar_reparacion_form.html', reparacion=reparacion, mecanicos=mecanicos)

@app.route('/reparaciones/finalizar/<int:reparacion_id>', methods=['POST'])
@login_required
def finalizar_reparacion_web(reparacion_id):
    """
    Permite finalizar una reparación.
    """
    print(f"DEBUG FLASK: Accediendo a finalizar_reparacion_web para ID: {reparacion_id}. Sesión: {session.get('username')}")
    
    reparacion = gestor_datos.obtener_reparacion_por_id(reparacion_id)
    if not reparacion:
        flash('Reparación no encontrada.', 'error')
        return redirect(url_for('en_taller'))

    today_date = date.today().isoformat()

    if gestor_datos.actualizar_estado_reparacion(
        reparacion_id, 'Completado', 
        fecha_salida=today_date, # Establecer la fecha de salida a hoy
        costo_total=reparacion['costo_total'] if reparacion['costo_total'] is not None else 0.0, # Mantener costo si ya lo tiene, sino 0
        costo_mano_obra=reparacion['costo_mano_obra'] if reparacion['costo_mano_obra'] is not None else 0.0,
        trabajos_realizados=reparacion['trabajos_realizados'],
        repuestos_usados=reparacion['repuestos_usados'],
        kilometraje_salida=reparacion['kilometraje_salida']
    ):
        flash('Reparación finalizada exitosamente.', 'success')
    else:
        flash('Error al finalizar la reparación.', 'error')
    
    return redirect(url_for('detalle_reparacion_web', reparacion_id=reparacion_id))


@app.route('/reparaciones/actualizar_estado/<int:reparacion_id>', methods=['GET', 'POST'])
@login_required
def actualizar_estado_reparacion_web(reparacion_id):
    reparacion = gestor_datos.obtener_reparacion_por_id(reparacion_id)
    if not reparacion:
        flash('Reparación no encontrada.', 'error')
        return redirect(url_for('vehiculos_en_taller'))

    if request.method == 'POST':
        estado = request.form['estado']
        trabajos_realizados = request.form.get('trabajos_realizados')
        repuestos_usados = request.form.get('repuestos_usados')
        costo_mano_obra = request.form.get('costo_mano_obra')
        costo_total = request.form.get('costo_total')
        fecha_salida = request.form.get('fecha_salida')
        kilometraje_salida = request.form.get('kilometraje_salida')

        try:
            costo_mano_obra = float(costo_mano_obra) if costo_mano_obra else None
            costo_total = float(costo_total) if costo_total else None
            kilometraje_salida = int(kilometraje_salida) if kilometraje_salida else None
        except ValueError:
            flash("Error: El costo o kilometraje deben ser números válidos.", 'error')
            return redirect(url_for('actualizar_estado_reparacion_web', reparacion_id=reparacion_id))

        if gestor_datos.actualizar_estado_reparacion(
            reparacion_id, estado, trabajos_realizados, repuestos_usados,
            costo_mano_obra, costo_total, fecha_salida, kilometraje_salida
        ):
            flash('Estado y detalles de reparación actualizados exitosamente.', 'success')
            return redirect(url_for('detalle_reparacion', reparacion_id=reparacion_id))
        else:
            flash('Error al actualizar la reparación.', 'error')
    
    return render_template('actualizar_reparacion_form.html', reparacion=reparacion)

@app.route('/api/cliente/<int:cliente_id>/vehiculos', methods=['GET'])
@login_required
def api_vehiculos_por_cliente(cliente_id):
    """API: Obtener vehículos por cliente (para carga dinámica en formularios, ej. agendar_turno.html)"""
    print(f"DEBUG FLASK: API solicitando vehículos para cliente ID: {cliente_id}")
    vehiculos = gestor_datos.obtener_vehiculos_por_cliente(cliente_id)
    if vehiculos:
        return jsonify({'success': True, 'vehiculos': [dict(v) for v in vehiculos]})
    return jsonify({'success': False, 'message': 'No se encontraron vehículos para este cliente.'})



@app.route('/taller')
@login_required 
def vehiculos_en_taller():
    vehiculos = gestor_datos.obtener_vehiculos_en_taller()
    return render_template('vehiculos_en_taller.html', vehiculos=vehiculos)

@app.route('/create_first_mecanico_once_only')
def create_first_mecanico():
    # ESTA RUTA DEBE SER REMOVIDA INMEDIATAMENTE DESPUÉS DE USARSE EN PRODUCCIÓN.
    # NUNCA MANTENGAS RUTAS DE CREACIÓN DE USUARIOS EXPUESTAS.
    username_admin = "Beto"
    password_admin = "1234" # CAMBIA ESTO POR ALGO FUERTE
    nombre_admin = "Andres"
    apellido_admin = "Esquivel"
    email_admin = "admin@taller.com"
    telefono_admin = "123456789"

    if gestor_datos.agregar_mecanico(nombre_admin, apellido_admin, telefono_admin, email_admin, username_admin, password_admin):
        return "Primer mecánico admin creado exitosamente. ¡ELIMINA ESTA RUTA DE TU CÓDIGO AHORA!"
    else:
        # Si ya existe, puedes intentar manejar el caso, o simplemente retornar un mensaje
        return "Error al crear el primer mecánico admin (posiblemente ya existe).", 409

# ==========================================================
# PUNTO DE ARRANQUE DE LA APLICACIÓN FLASK (AJUSTADO PARA DESPLIEGUE LOCAL)
# ==========================================================
if __name__ == '__main__':
    gestor_datos.crear_tablas() # Las tablas se crearán en la base de datos local (sqlite por defecto)
    '''
    # Ejecutar la aplicación Flask para desarrollo local
    # host='127.0.0.1' (o localhost) para que solo sea accesible desde tu máquina
    # port=5000 es el puerto por defecto de Flask
    # debug=True: Habilita el modo de depuración. Esto te dará mensajes de error detallados
    # y recargará el servidor automáticamente cuando hagas cambios en el código.
    # ¡Recuerda poner debug=False para producción!
    app.run(host='127.0.0.1', port=5000, debug=True)'''
    port = int(os.environ.get("PORT", 5000))
    
    app.run(host="0.0.0.0", port=port, debug=False)

