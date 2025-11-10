// app/frontend/app.js

// --- 1. CONSTANTES ---
const API_URL = "/api/dashboard-data";
const USER_INFO_URL = "/api/user-info";

// --- 2. FUNCIONES DE AUTENTICACIÓN ---

/**
 * Comprueba si el usuario está "logeado" (en localStorage).
 * Si no, lo redirige a la página de login.
 * Devuelve 'true' si está autenticado, 'false' si no.
 */
function checkAuthentication() {
    const user = localStorage.getItem('magic_user_username');
    if (!user) {
        console.log("Usuario no encontrado, redirigiendo al login...");
        window.location.href = '/login';
        return false;
    }
    return true;
}

/**
 * Obtiene los headers de autenticación desde localStorage
 * para enviarlos en CADA petición de la API.
 */
function getAuthHeaders() {
    return {
        'X-User-Username': localStorage.getItem('magic_user_username') || '',
        'X-User-Role': localStorage.getItem('magic_user_role') || ''
    };
}

// --- 3. FUNCIONES DE CARGA DE DATOS (CON HEADERS) ---

/**
 * Llama a la API de /api/user-info una sola vez.
 */
// app/frontend/app.js

async function fetchUserInfo() {
    console.log("Obteniendo info del usuario...");
    try {
        // ... (el 'try' está bien)
        const response = await fetch(USER_INFO_URL, {
            headers: getAuthHeaders()
        });
        // ... (el resto del 'try' está bien)
        const data = await response.json();
        updateUserInfo(data);

    } catch (error) {
        console.error("Error al obtener info del usuario:", error);

        // --- ¡BLOQUE 'CATCH' CORREGIDO! ---
        // No reemplazamos todo el HTML, solo actualizamos el texto.
        document.getElementById('user-name').innerText = "Error";
        document.getElementById('user-role').innerText = "Error";

        const permissionsList = document.getElementById('user-permissions');
        permissionsList.innerHTML = ""; // Limpiar "cargando"
        const li = document.createElement('li');
        li.textContent = "Error al cargar el perfil.";
        li.style.color = "#e63946"; // Rojo
        permissionsList.appendChild(li);

        // ¡Ya NO borramos el botón de "Cerrar Sesión"!
    }
}

/**
 * Función principal para obtener datos de la API (tabla y gráfico).
 */
async function fetchData() {
    console.log("Llamando a la API de FastAPI...");
    try {
        // --- ¡ASEGÚRATE DE QUE ESTA PETICIÓN TAMBIÉN ENVÍA HEADERS! ---
        const response = await fetch(API_URL, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
             window.location.href = '/login'; // Sesión expirada o inválida
             return;
        }
        if (!response.ok) throw new Error(`Error de red: ${response.statusText}`);

        const data = await response.json();
        updateAuditTable(data.table);
        updatePerformanceChart(data.chart);
    } catch (error) {
        console.error("Error al obtener datos del dashboard:", error);
    }
}

// --- 4. FUNCIONES DE ACTUALIZACIÓN DE LA UI (PEGAR CÓDIGO FALTANTE) ---
// (Estas funciones rellenan el HTML)

/**
 * Actualiza la tarjeta de perfil de usuario con los datos de la API.
 */
function updateUserInfo(userData) {
    document.getElementById('user-name').innerText = userData.username;
    document.getElementById('user-role').innerText = userData.role;

    const permissionsList = document.getElementById('user-permissions');
    permissionsList.innerHTML = ""; // Limpiar "Cargando..."

    if (userData.permissions.length === 0) {
        permissionsList.innerHTML = "<li>Sin permisos asignados.</li>";
    } else {
        userData.permissions.sort().forEach(perm => {
            const li = document.createElement('li');
            if (perm.includes('cast')) li.textContent = `🪄 ${perm}`;
            else if (perm.includes('read')) li.textContent = `📖 ${perm}`;
            else li.textContent = `⚙️ ${perm}`;
            permissionsList.appendChild(li);
        });
    }
}

/**
 * Actualiza la tabla de auditoría con nuevos datos.
 */
function updateAuditTable(tableData) {
    const tableBody = document.getElementById('auditTable').querySelector('tbody');
    tableBody.innerHTML = ""; // Limpiar tabla

    if (tableData.error) {
        tableBody.innerHTML = `<tr><td colspan="4">Error al cargar logs: ${tableData.error}</td></tr>`;
        return;
    }

    // Si no hay datos, mostrar un mensaje
    if (Object.keys(tableData).length === 0) {
        tableBody.innerHTML = `<tr><td colspan="4">Aún no se han registrado eventos.</td></tr>`;
        return;
    }

    for (const spellName in tableData) {
        const counts = tableData[spellName];
        const row = `
            <tr>
                <td>${spellName}</td>
                <td>${counts.INTENTO}</td>
                <td>${counts.ÉXITO}</td>
                <td>${counts.FALLO}</td>
            </tr>
        `;
        tableBody.innerHTML += row;
    }
}

/**
 * Actualiza el gráfico en tiempo real.
 */
function updatePerformanceChart(chartData) {
    // (Este código asume que tienes 'performanceChart' definido globalmente)
    try {
        const now = new Date();
        const timeLabel = now.toLocaleTimeString();
        const chart = performanceChart.data;

        chart.labels.push(timeLabel);
        chart.datasets[0].data.push(chartData.current_latency_ms);
        chart.datasets[1].data.push(chartData.events_per_second);

        const maxDataPoints = 10;
        if (chart.labels.length > maxDataPoints) {
            chart.labels.shift();
            chart.datasets[0].data.shift();
            chart.datasets[1].data.shift();
        }
        performanceChart.update();
        document.getElementById('metric-latency').innerText = chartData.current_latency_ms;
        document.getElementById('metric-events').innerText = chartData.events_per_second;
    } catch (e) {
        console.error("Error al actualizar el gráfico:", e);
    }
}

// --- 5. INICIALIZACIÓN DEL GRÁFICO (PEGAR CÓDIGO FALTANTE) ---

// (Asegúrate de que este código esté ANTES del 'DOMContentLoaded')
const ctx = document.getElementById('performanceChart').getContext('2d');
const performanceChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Latencia (ms)',
            data: [],
            borderColor: 'rgb(255, 215, 0)',
            backgroundColor: 'rgba(255, 215, 0, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            yAxisID: 'yLatency',
        }, {
            label: 'Eventos/seg',
            data: [],
            borderColor: 'rgb(0, 191, 255)',
            backgroundColor: 'rgba(0, 191, 255, 0.1)',
            borderWidth: 2,
            tension: 0.4,
            yAxisID: 'yEvents',
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            yLatency: { type: 'linear', position: 'left', ticks: { color: '#e0e0e0' }, grid: { color: '#4a4a7c' }},
            yEvents: { type: 'linear', position: 'right', ticks: { color: '#e0e0e0' }, grid: { color: 'transparent' }},
            x: { ticks: { color: '#e0e0e0' }, grid: { color: '#4a4a7c' }}
        },
        plugins: { legend: { labels: { color: '#e0e0e0' }}}
    }
});


// --- 6. EJECUCIÓN ---
document.addEventListener('DOMContentLoaded', () => {

    // 1. Comprueba si el usuario está autenticado.
    const isAuthenticated = checkAuthentication();

    // 2. Si NO lo está, detén la ejecución
    if (!isAuthenticated) {
        return;
    }

    // 3. Si SÍ lo está, carga los datos del dashboard.
    console.log("Usuario autenticado, cargando dashboard...");
    fetchData();
    fetchUserInfo();

    // Configurar la actualización en "tiempo real" (polling)
    setInterval(fetchData, 5000);

    // Lógica para el botón de Cerrar Sesión
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            console.log("Cerrando sesión...");
            localStorage.clear();
            window.location.href = '/login';
        });
    }
});