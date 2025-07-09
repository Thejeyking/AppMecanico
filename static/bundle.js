// static_cliente/bundle.js - Aplicación React Completa

// *** VERIFICACIÓN CRÍTICA: Asegúrate de que React y ReactDOM estén cargados. ***
// Estas verificaciones se ejecutan cuando el script se carga.
// Son importantes para depurar si los CDN no se cargan correctamente en el index.html.
if (typeof window.React === 'undefined') {
    console.error("ERROR CRÍTICO: 'window.React' no se ha cargado. Verifica el script CDN de React en tu index.html.");
    document.getElementById('root').innerHTML = '<div style="text-align: center; color: red; font-size: 1.5em; padding-top: 50px;">Error al cargar la aplicación: React no disponible. Por favor, contacta a soporte (React CDN missing).</div>';
    throw new Error("window.React no está cargado.");
}
if (typeof window.ReactDOM === 'undefined') {
    console.error("ERROR CRÍTICO: 'window.ReactDOM' no se ha cargado. Verifica el script CDN de ReactDOM en tu index.html.");
    document.getElementById('root').innerHTML = '<div style="text-align: center; color: red; font-size: 1.5em; padding-top: 50px;">Error al cargar la aplicación: ReactDOM no disponible. Por favor, contacta a soporte (ReactDOM CDN missing).</div>';
    throw new Error("window.ReactDOM no está cargado.");
}

// Acceder a las variables globales de React y ReactDOM proporcionadas por el CDN
const React = window.React;
const ReactDOM = window.ReactDOM;

// Base URL para las APIs de Flask (se obtiene automáticamente del dominio actual)
const API_BASE_URL = window.location.origin;

// Sonido para notificaciones (La URL externa fue eliminada. Puedes usar un sonido local
// si lo agregas a la carpeta static_cliente, o dejarlo así para que no reproduzca sonido.)
const notificationSound = {
    play: () => { console.log("Sonido de notificación (deshabilitado el externo)."); }
};


// --- Componentes React ---

/**
 * Componente para el formulario de inicio de sesión de clientes.
 * Permite al usuario ingresar su nombre de usuario y contraseña.
 * @param {object} props - Propiedades del componente.
 * @param {function} props.onLoginSuccess - Función a llamar al iniciar sesión exitosamente, pasando el cliente_id.
 * @param {function} props.onNavigateToRegister - Función a llamar para navegar a la vista de registro.
 */
const LoginComponent = ({ onLoginSuccess, onNavigateToRegister }) => {
    const [username, setUsername] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [message, setMessage] = React.useState('');

    const handleLogin = async (e) => {
        e.preventDefault(); // Previene el comportamiento por defecto del formulario
        setMessage(''); // Limpia mensajes anteriores

        try {
            const response = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }) // Envía credenciales como JSON
            });
            const data = await response.json(); // Parsea la respuesta JSON
            if (data.success) {
                setMessage(data.message);
                onLoginSuccess(data.cliente_id); // Llama a la función de éxito con el ID del cliente
            } else {
                setMessage(data.message); // Muestra el mensaje de error del servidor
            }
        } catch (error) {
            setMessage('Error de conexión. Inténtalo de nuevo.');
            console.error('Error de login:', error);
        }
    };

    return (
        React.createElement("div", { className: "flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4" },
            React.createElement("div", { className: "bg-white p-8 rounded-lg shadow-lg w-full max-w-md" },
                React.createElement("h2", { className: "text-2xl font-bold text-center mb-6 text-gray-800" }, "Iniciar Sesión Cliente"),
                // Muestra mensajes de error o éxito
                message && React.createElement("p", { className: "mb-4 text-center text-red-500" }, message),
                React.createElement("form", { onSubmit: handleLogin, className: "space-y-4" },
                    React.createElement("div", { className: "form-group" },
                        React.createElement("label", { htmlFor: "username", className: "block text-gray-700 text-sm font-bold mb-2" }, "Usuario:"),
                        React.createElement("input", {
                            type: "text",
                            id: "username",
                            className: "w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                            value: username,
                            onChange: (e) => setUsername(e.target.value),
                            required: true
                        })
                    ),
                    React.createElement("div", { className: "form-group" },
                        React.createElement("label", { htmlFor: "password", className: "block text-gray-700 text-sm font-bold mb-2" }, "Contraseña:"),
                        React.createElement("input", {
                            type: "password",
                            id: "password",
                            className: "w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                            value: password,
                            onChange: (e) => setPassword(e.target.value),
                            required: true
                        })
                    ),
                    React.createElement("button", { type: "submit", className: "w-full bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 transition duration-300" }, "Entrar")
                ),
                React.createElement("p", { className: "text-center mt-6 text-gray-600" },
                    "¿No tienes cuenta? ",
                    React.createElement("button", { onClick: onNavigateToRegister, className: "text-blue-600 hover:underline" }, "Regístrate aquí")
                )
            )
        )
    );
};

/**
 * Componente para el formulario de registro de nuevos clientes.
 * Permite a los usuarios crear una cuenta en el sistema.
 * @param {object} props - Propiedades del componente.
 * @param {function} props.onRegisterSuccess - Función a llamar al registrarse exitosamente.
 * @param {function} props.onNavigateToLogin - Función a llamar para navegar a la vista de login.
 */
const RegisterComponent = ({ onRegisterSuccess, onNavigateToLogin }) => {
    const [username, setUsername] = React.useState('');
    const [password, setPassword] = React.useState('');
    // Nombres de estado que coinciden directamente con las claves esperadas por Flask
    const [nombre_cliente, setNombreCliente] = React.useState(''); 
    const [apellido_cliente, setApellidoCliente] = React.useState('');
    const [message, setMessage] = React.useState('');

    const handleRegister = async (e) => {
        e.preventDefault();
        setMessage('');
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/registro`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    nombre_cliente: nombre_cliente, // Asegura que la clave JSON coincide con Flask
                    apellido_cliente: apellido_cliente // Asegura que la clave JSON coincide con Flask
                })
            });
            const data = await response.json();
            if (data.success) {
                setMessage(data.message + ' Ahora puedes iniciar sesión.');
                // Limpia los campos del formulario tras un registro exitoso
                setUsername('');
                setPassword('');
                setNombreCliente('');
                setApellidoCliente('');
                // Redirige al login después de un breve retraso
                setTimeout(onNavigateToLogin, 2000);
            } else {
                setMessage(data.message); // Muestra el mensaje de error del servidor
            }
        } catch (error) {
            setMessage('Error de conexión. Inténtalo de nuevo.');
            console.error('Error de registro:', error);
        }
    };

    return (
        React.createElement("div", { className: "flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4" },
            React.createElement("div", { className: "bg-white p-8 rounded-lg shadow-lg w-full max-w-md" },
                React.createElement("h2", { className: "text-2xl font-bold text-center mb-6 text-gray-800" }, "Registrar Cliente"),
                message && React.createElement("p", { className: "mb-4 text-center text-red-500" }, message),
                React.createElement("form", { onSubmit: handleRegister, className: "space-y-4" },
                    React.createElement("div", { className: "form-group" },
                        React.createElement("label", { htmlFor: "reg-username", className: "block text-gray-700 text-sm font-bold mb-2" }, "Usuario:"),
                        React.createElement("input", {
                            type: "text",
                            id: "reg-username",
                            className: "w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                            value: username,
                            onChange: (e) => setUsername(e.target.value),
                            required: true
                        })
                    ),
                    React.createElement("div", { className: "form-group" },
                        React.createElement("label", { htmlFor: "reg-password", className: "block text-gray-700 text-sm font-bold mb-2" }, "Contraseña:"),
                        React.createElement("input", {
                            type: "password",
                            id: "reg-password",
                            className: "w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                            value: password,
                            onChange: (e) => setPassword(e.target.value),
                            required: true
                        })
                    ),
                    React.createElement("div", { className: "form-group" },
                        React.createElement("label", { htmlFor: "cliente-nombre", className: "block text-gray-700 text-sm font-bold mb-2" }, "Tu Nombre (como en el taller):"),
                        React.createElement("input", {
                            type: "text",
                            id: "cliente-nombre",
                            className: "w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                            value: nombre_cliente,
                            onChange: (e) => setNombreCliente(e.target.value),
                            placeholder: "Ej. Juan",
                            required: true
                        })
                    ),
                    React.createElement("div", { className: "form-group" },
                        React.createElement("label", { htmlFor: "cliente-apellido", className: "block text-gray-700 text-sm font-bold mb-2" }, "Tu Apellido (como en el taller):"),
                        React.createElement("input", {
                            type: "text",
                            id: "cliente-apellido",
                            className: "w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                            value: apellido_cliente,
                            onChange: (e) => setApellidoCliente(e.target.value),
                            placeholder: "Ej. Pérez",
                            required: true
                        }),
                        React.createElement("small", { className: "text-gray-500 text-xs mt-1" }, "Asegúrate de usar el mismo nombre y apellido que tienes registrado en el taller.")
                    ),
                    React.createElement("button", { type: "submit", className: "w-full bg-green-600 text-white p-2 rounded-md hover:bg-green-700 transition duration-300" }, "Registrar")
                ),
                React.createElement("p", { className: "text-center mt-6 text-gray-600" },
                    "¿Ya tienes cuenta? ",
                    React.createElement("button", { onClick: onNavigateToLogin, className: "text-blue-600 hover:underline" }, "Inicia Sesión")
                )
            )
        )
    );
};

/**
 * Componente del Dashboard del Cliente.
 * Muestra los datos del cliente y una lista de sus vehículos registrados.
 * @param {object} props - Propiedades del componente.
 * @param {object} props.cliente - Objeto con los datos del cliente.
 * @param {Array<object>} props.vehiculos - Array de objetos con los datos de los vehículos del cliente.
 * @param {function} props.onSelectVehicle - Función a llamar al seleccionar un vehículo para ver sus detalles.
 * @param {function} props.onLogout - Función a llamar para cerrar la sesión.
 */
const DashboardComponent = ({ cliente, vehiculos, onSelectVehicle, onLogout }) => {
    // Estados internos para asegurar que los datos se actualizan si las props cambian
    const [clienteDataState, setClienteDataState] = React.useState(cliente);
    const [vehiculosDataState, setVehiculosDataState] = React.useState(vehiculos);

    React.useEffect(() => {
        setClienteDataState(cliente);
        setVehiculosDataState(vehiculos);
    }, [cliente, vehiculos]); // Se ejecuta cuando 'cliente' o 'vehiculos' cambian

    if (!clienteDataState || !vehiculosDataState) {
        return React.createElement("div", { className: "text-center p-8" }, "Cargando datos del cliente...");
    }

    return (
        React.createElement("div", { className: "container mx-auto p-4 md:p-8 bg-white rounded-lg shadow-lg mt-8" },
            React.createElement("div", { className: "flex justify-between items-center mb-6" },
                React.createElement("h2", { className: "text-3xl font-bold text-gray-800" }, `Bienvenido, ${clienteDataState.nombre} ${clienteDataState.apellido}`),
                React.createElement("button", { onClick: onLogout, className: "bg-red-500 text-white p-2 rounded-md hover:bg-red-600 transition duration-300" }, "Cerrar Sesión")
            ),
            React.createElement("h3", { className: "text-2xl font-semibold mb-4 text-gray-700" }, "Tus Vehículos:"),
            vehiculosDataState.length === 0 ? (
                React.createElement("p", { className: "text-gray-600" }, "No tienes vehículos registrados. Contacta al taller.")
            ) : (
                React.createElement("div", { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" },
                    vehiculosDataState.map(vehiculo => (
                        React.createElement("div", {
                            key: vehiculo.id,
                            className: "bg-blue-50 p-6 rounded-lg shadow-md hover:shadow-lg transition duration-300 cursor-pointer border border-blue-200",
                            onClick: () => {
                                console.log("DEBUG: Vehiculo seleccionado ID:", vehiculo.id);
                                onSelectVehicle(vehiculo); // Pasa el vehículo seleccionado
                            }
                        },
                            React.createElement("h4", { className: "text-xl font-bold text-blue-800 mb-2" }, `${vehiculo.marca} ${vehiculo.modelo}`),
                            React.createElement("p", { className: "text-lg text-gray-700" }, "Patente: ", React.createElement("span", { className: "font-semibold" }, vehiculo.patente)),
                            React.createElement("p", { className: "text-sm text-gray-600" }, `Año: ${vehiculo.anio}`),
                            React.createElement("p", { className: "text-sm text-gray-600" }, `KM inicial: ${vehiculo.kilometraje_inicial}`),
                            React.createElement("button", { className: "mt-4 bg-blue-500 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-600 transition duration-300" }, "Ver Detalles")
                        )
                    ))
                )
            )
        )
    );
};

/**
 * Componente para mostrar los detalles de un vehículo y su historial de reparaciones.
 * También muestra el estado actual de la reparación si el vehículo está en taller.
 * @param {object} props - Propiedades del componente.
 * @param {object} props.vehicle - Objeto con los datos del vehículo seleccionado.
 * @param {function} props.onBackToDashboard - Función a llamar para volver al dashboard.
 */
const VehicleDetailComponent = ({ vehicle, onBackToDashboard }) => {
    const [historial, setHistorial] = React.useState([]);
    const [activeRepair, setActiveRepair] = React.useState(null);
    const [message, setMessage] = React.useState('');
    const [pollingInterval, setPollingInterval] = React.useState(null);
    const [lastKnownStatus, setLastKnownStatus] = React.useState(null); // Para notificaciones de cambio de estado

    // Función asíncrona para obtener el estado actual y el historial del vehículo
    const fetchVehicleData = async () => {
        setMessage(''); // Limpia mensajes anteriores
        try {
            // Petición para obtener el Historial de Reparaciones
            const historialResponse = await fetch(`${API_BASE_URL}/api/vehiculo/${vehicle.id}/historial`);
            const historialData = await historialResponse.json();
            console.log("DEBUG REACT: Respuesta historial:", historialData);
            if (historialData.success) {
                setHistorial(historialData.historial);
            } else {
                setMessage('Error al cargar el historial: ' + (historialData.message || 'Error desconocido.'));
                console.error("DEBUG REACT: Error en historial API:", historialData);
            }

            // Petición para obtener el Estado Activo de la Reparación
            const activeResponse = await fetch(`${API_BASE_URL}/api/vehiculo/${vehicle.id}/estado_activo`);
            const activeData = await activeResponse.json();
            console.log("DEBUG REACT: Respuesta estado activo:", activeData);
            if (activeData.success && activeData.reparacion) {
                setActiveRepair(activeData.reparacion);
                // Lógica para reproducir un sonido si el estado de la reparación ha cambiado
                if (lastKnownStatus && lastKnownStatus !== activeData.reparacion.estado) {
                    notificationSound.play(); 
                    alert(`¡Actualización de estado para ${vehicle.patente}! Nuevo estado: ${activeData.reparacion.estado}`);
                }
                setLastKnownStatus(activeData.reparacion.estado); // Actualiza el último estado conocido
            } else {
                setActiveRepair(null); // No hay reparación activa
                setLastKnownStatus(null);
                setMessage('No hay reparación activa para este vehículo.');
                console.error("DEBUG REACT: Error en estado activo API o no hay datos:", activeData);
            }
        } catch (error) {
            setMessage('Error de conexión al cargar datos del vehículo.');
            console.error('DEBUG REACT: Error en fetch general:', error);
        }
    };

    React.useEffect(() => {
        console.log("DEBUG: VehicleDetailComponent montado. ID del vehículo:", vehicle.id);
        fetchVehicleData(); // Carga inicial de datos al montar el componente

        // Configura un intervalo para "polling" (obtener actualizaciones periódicamente)
        const interval = setInterval(fetchVehicleData, 15000); // Poll cada 15 segundos
        setPollingInterval(interval);

        // Función de limpieza: se ejecuta al desmontar el componente para limpiar el intervalo
        return () => {
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
        };
    }, [vehicle.id]); // El efecto se re-ejecuta si el ID del vehículo cambia

    if (!vehicle) {
        return React.createElement("div", { className: "text-center p-8" }, "Seleccione un vehículo.");
    }

    return (
        React.createElement("div", { className: "container mx-auto p-4 md:p-8 bg-white rounded-lg shadow-lg mt-8" },
            React.createElement("button", { onClick: onBackToDashboard, className: "bg-gray-500 text-white p-2 rounded-md hover:bg-gray-600 transition duration-300 mb-6" }, "← Volver al Dashboard"),
            React.createElement("h2", { className: "text-3xl font-bold text-gray-800 mb-4" }, `Detalles del Vehículo: ${vehicle.patente}`),
            React.createElement("p", { className: "text-xl text-gray-700 mb-6" }, `${vehicle.marca} ${vehicle.modelo} (${vehicle.anio})`),
            message && React.createElement("p", { className: "mb-4 text-center text-red-500" }, message),
            React.createElement("h3", { className: "text-2xl font-semibold mb-4 text-gray-700" }, "Estado Actual en Taller:"),
            activeRepair ? (
                React.createElement("div", { className: "bg-yellow-50 p-6 rounded-lg shadow-md border border-yellow-200 mb-8" },
                    React.createElement("p", { className: "text-lg font-bold text-yellow-800 mb-2" }, `Estado: ${activeRepair.estado}`),
                    React.createElement("p", { className: "text-gray-700" }, `Fecha de Ingreso: ${activeRepair.fecha_ingreso}`),
                    React.createElement("p", { className: "text-gray-700" }, `Problema Reportado: ${activeRepair.problema_reportado}`),
                    React.createElement("p", { className: "text-gray-700" }, `Trabajos Realizados: ${activeRepair.trabajos_realizados || 'N/A'}`),
                    React.createElement("p", { className: "text-gray-700" }, `Repuestos Usados: ${activeRepair.repuestos_usados || 'N/A'}`),
                    React.createElement("p", { className: "text-gray-700" }, `Costo Acumulado: $${activeRepair.costo_total || '0.00'}`),
                    React.createElement("p", { className: "text-gray-700" }, `Mecánico: ${activeRepair.nombre_mecanico} ${activeRepair.apellido_mecanico || 'N/A'}`)
                )
            ) : (
                React.createElement("p", { className: "text-gray-600 mb-8" }, "Este vehículo no tiene una reparación activa en este momento.")
            ),
            React.createElement("h3", { className: "text-2xl font-semibold mb-4 text-gray-700" }, "Historial de Reparaciones:"),
            historial.length === 0 ? (
                React.createElement("p", { className: "text-gray-600" }, "No hay historial de reparaciones para este vehículo.")
            ) : (
                React.createElement("div", { className: "space-y-6" },
                    historial.map(reparacion => (
                        React.createElement("div", { key: reparacion.id, className: "bg-blue-50 p-6 rounded-lg shadow-md border border-blue-200" },
                            React.createElement("p", { className: "text-lg font-bold text-blue-800 mb-2" }, `ID Reparación: ${reparacion.id} - Estado: ${reparacion.estado}`),
                            React.createElement("p", { className: "text-gray-700" }, `Fecha de Ingreso: ${reparacion.fecha_ingreso}`),
                            React.createElement("p", { className: "text-gray-700" }, `Kilometraje Ingreso: ${reparacion.kilometraje_ingreso} km`),
                            React.createElement("p", { className: "text-gray-700" }, `Problema Reportado: ${reparacion.problema_reportado}`),
                            React.createElement("p", { className: "text-gray-700" }, `Trabajos Realizados: ${reparacion.trabajos_realizados || 'N/A'}`),
                            React.createElement("p", { className: "text-gray-700" }, `Repuestos Usados: ${reparacion.repuestos_usados || 'N/A'}`),
                            React.createElement("p", { className: "text-gray-700" }, `Costo Total: $${reparacion.costo_total || '0.00'}`),
                            React.createElement("p", { className: "text-gray-700" }, `Mecánico: ${reparacion.nombre_mecanico} ${reparacion.apellido_mecanico || 'N/A'}`)
                        )
                    ))
                )
            )
        )
    );
};

/**
 * Componente principal de la aplicación React.
 * Gestiona la lógica de enrutamiento y estado de la aplicación.
 */
const App = () => {
    const [isLoggedIn, setIsLoggedIn] = React.useState(false);
    const [clienteId, setClienteId] = React.useState(null);
    const [clienteData, setClienteData] = React.useState(null);
    const [vehiculosData, setVehiculosData] = React.useState([]);
    const [selectedVehicle, setSelectedVehicle] = React.useState(null); 
    const [currentView, setCurrentView] = React.useState('login'); // Vista inicial: login

    // Efecto para verificar la sesión del usuario al cargar la aplicación
    React.useEffect(() => {
        const checkSession = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/check_session`);
                const contentType = response.headers.get("content-type");
                // Asegura que la respuesta es JSON para evitar errores de parseo
                if (contentType && contentType.includes("application/json")) {
                    const data = await response.json();
                    if (data.logged_in) {
                        setIsLoggedIn(true);
                        setClienteId(data.cliente_id);
                        setCurrentView('dashboard'); // Si está logueado, va al dashboard
                    } else {
                        setIsLoggedIn(false);
                        setCurrentView('login'); // Si no, permanece en el login
                    }
                } else {
                    // Si la respuesta no es JSON, indica un posible error del servidor
                    const text = await response.text();
                    console.error("ERROR: La API /api/check_session devolvió HTML en lugar de JSON:", text.substring(0, 200) + "...");
                    throw new Error("Unexpected HTML response from /api/check_session");
                }
            } catch (error) {
                console.error('Error al verificar sesión:', error);
                // Si hay un error de red o de parseo, fuerza el estado a no logueado
                if (error.message.includes("Unexpected HTML response") || error.message.includes("Unexpected token '<'")) {
                    console.error("DEBUG: La API de sesión devolvió HTML. Forzando cierre de sesión.");
                }
                setIsLoggedIn(false);
                setCurrentView('login');
            }
        };
        checkSession();
    }, []); // Se ejecuta solo una vez al montar el componente

    // Efecto para cargar los datos del dashboard si el usuario está logueado
    React.useEffect(() => {
        const fetchDashboardData = async () => {
            if (isLoggedIn && clienteId) {
                console.log("DEBUG: Fetching dashboard data for clienteId:", clienteId);
                try {
                    const response = await fetch(`${API_BASE_URL}/api/cliente/dashboard`);
                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.indexOf("application/json") !== -1) {
                        const data = await response.json();
                        if (data.success) {
                            setClienteData(data.cliente);
                            setVehiculosData(data.vehiculos);
                            console.log("DEBUG: Dashboard data loaded successfully.");
                        } else {
                            console.error('Error al cargar dashboard:', data.message);
                            handleLogout(); // Si hay un error al cargar el dashboard, cierra sesión
                        }
                    } else {
                        const text = await response.text();
                        console.error("ERROR: La API /api/cliente/dashboard devolvió HTML:", text);
                        handleLogout(); 
                    }
                } catch (error) {
                    console.error('Error de conexión al cargar dashboard:', error);
                    handleLogout(); // Si hay un error de conexión, cierra sesión
                }
            }
        };
        fetchDashboardData();
    }, [isLoggedIn, clienteId]); // Se ejecuta cuando el estado de login o el ID del cliente cambian

    // Callback para cuando el login es exitoso
    const handleLoginSuccess = (id) => {
        setClienteId(id);
        setIsLoggedIn(true);
        setCurrentView('dashboard');
    };

    // Callback para cerrar la sesión del usuario
    const handleLogout = async () => {
        try {
            await fetch(`${API_BASE_URL}/api/logout`); // Llama a la API de logout
            setIsLoggedIn(false);
            setClienteId(null);
            setClienteData(null);
            setVehiculosData([]);
            setSelectedVehicle(null);
            setCurrentView('login'); // Vuelve a la vista de login
            console.log("DEBUG: Sesión cerrada y estado reseteado.");
        } catch (error) {
            console.error('Error al cerrar sesión:', error);
        }
    };

    // Callback para seleccionar un vehículo y cambiar a la vista de detalles
    const handleSelectVehicle = (vehicle) => {
        setSelectedVehicle(vehicle);
        setCurrentView('vehicleDetail');
    };

    // Callback para volver al dashboard desde la vista de detalles del vehículo
    const handleBackToDashboard = () => {
        setSelectedVehicle(null);
        setCurrentView('dashboard');
    };

    // Función que renderiza el componente actual según la vista
    const renderContent = () => {
        console.log("DEBUG: renderContent - currentView:", currentView);
        // Verificaciones adicionales para asegurar que los componentes están definidos
        if (typeof LoginComponent !== 'function' || typeof RegisterComponent !== 'function' || typeof DashboardComponent !== 'function' || typeof VehicleDetailComponent !== 'function') {
            console.error("ERROR: Uno o más componentes no son funciones. React no se ha inicializado correctamente.");
            return <div style={{textAlign: 'center', color: 'red', fontSize: '1.5em', paddingTop: '50px'}}>Error interno: Componentes de la aplicación no válidos.</div>;
        }

        switch (currentView) {
            case 'login':
                return React.createElement(LoginComponent, { onLoginSuccess: handleLoginSuccess, onNavigateToRegister: () => setCurrentView('register') });
            case 'register':
                return React.createElement(RegisterComponent, { onRegisterSuccess: () => setCurrentView('login'), onNavigateToLogin: () => setCurrentView('login') });
            case 'dashboard':
                return isLoggedIn && clienteData ? (
                    React.createElement(DashboardComponent, { cliente: clienteData, vehiculos: vehiculosData, onSelectVehicle: handleSelectVehicle, onLogout: handleLogout })
                ) : (
                    React.createElement('div', { className: 'text-center p-8' }, 'Cargando dashboard...')
                );
            case 'vehicleDetail':
                return selectedVehicle ? (
                    React.createElement(VehicleDetailComponent, { vehicle: selectedVehicle, onBackToDashboard: handleBackToDashboard })
                ) : (
                    React.createElement('div', { className: "text-center p-8" }, 'Vehículo no seleccionado.')
                );
            default:
                // Por defecto, muestra el login si la vista no es reconocida
                return React.createElement(LoginComponent, { onLoginSuccess: handleLoginSuccess, onNavigateToRegister: () => setCurrentView('register') });
        }
    };

    return (
        React.createElement('div', { className: 'min-h-screen bg-gray-100' },
            renderContent()
        )
    );
};

// Renderizar la aplicación React al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
    const rootElement = document.getElementById('root');
    if (rootElement) {
        console.log("DEBUG: Elemento 'root' encontrado. Intentando montar la aplicación React.");
        try {
            if (typeof App === 'function') {
                const root = ReactDOM.createRoot(rootElement);
                root.render(
                    React.createElement(React.StrictMode, null,
                        React.createElement(App, null)
                    )
                );
                console.log("DEBUG: Aplicación React montada exitosamente.");
            } else {
                console.error("ERROR CRÍTICO: El componente 'App' no es una función al momento de renderizar. Esto puede ocurrir si el script no se cargó completamente o hay un error de sintaxis temprano.");
                rootElement.innerHTML = '<div style="text-align: center; color: red; font-size: 1.5em; padding-top: 50px;">Error grave al iniciar la aplicación. Componente App no válido.</div>';
            }
        } catch (e) {
            console.error("ERROR CRÍTICO: Fallo al montar la aplicación React. Verifica tu componente App y la estructura.", e);
            rootElement.innerHTML = '<div style="text-align: center; color: red; font-size: 1.5em; padding-top: 50px;">Error grave al iniciar la aplicación. Consulta la consola para más detalles.</div>';
        }
    } else {
        console.error("ERROR CRÍTICO: No se encontró el elemento con ID 'root' en el HTML. La aplicación React no puede montarse.");
    }
});
