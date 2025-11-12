// app/frontend/app.js

// --- 1. CONSTANTES GLOBALES ---
const API_URL = "/api/dashboard-data";
const USER_INFO_URL = "/api/user-info";

// --- 2. DECLARACIÓN DE VARIABLES GLOBALES ---
let performanceChart;

// --- 3. FUNCIONES DE AUTENTICACIÓN ---

function checkAuthentication() {
    // ¡IMPORTANTE! Lee los datos de sessionStorage
    const user = sessionStorage.getItem('magic_user_username');

    if (!user) {
        console.log("checkAuthentication falló: No se encontró usuario. Redirigiendo a /");
        window.location.href = '/'; // Redirige a la raíz (login)
        return false;
    }
    console.log("checkAuthentication OK. Usuario:", user);
    return true;
}

function getAuthHeaders() {
    return {
        'X-User-Username': sessionStorage.getItem('magic_user_username') || '',
        'X-User-Role': sessionStorage.getItem('magic_user_role') || ''
    };
}

// --- 4. FUNCIONES DE CARGA DE DATOS (FETCH) ---

async function fetchUserInfo() {
    console.log("fetchUserInfo: Obteniendo info del usuario...");
    try {
        const response = await fetch(USER_INFO_URL, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
             console.log("fetchUserInfo: Error 401. Redirigiendo a /");
             window.location.href = '/';
             return;
        }
        if (!response.ok) throw new Error(`Error de red: ${response.statusText}`);

        const data = await response.json();
        updateUserInfo(data);

    } catch (error) {
        console.error("Error al obtener info del usuario:", error);
        document.getElementById('user-name').innerText = "Error";
        document.getElementById('user-role').innerText = "Error";
        const permissionsList = document.getElementById('user-permissions');
        permissionsList.innerHTML = "<li>Error al cargar el perfil.</li>";
        permissionsList.style.color = "#e63946";
    }
}

async function fetchData() {
    console.log("fetchData: Obteniendo datos del dashboard...");
    try {
        const response = await fetch(API_URL, {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
             console.log("fetchData: Error 401. Redirigiendo a /");
             window.location.href = '/';
             return;
        }
        if (!response.ok) throw new Error(`Error de red: ${response.statusText}`);

        const data = await response.json();
        updateAuditTable(data.table);
        updatePerformanceChart(data.chart);
    } catch (error) {
        console.error("Error al obtener datos del dashboard:", error);
        if (error.message.includes("Failed to fetch")) {
            console.log("Servidor no responde. Cerrando sesión.");
            sessionStorage.clear();
            window.location.href = '/';
        }
    }
}

async function castSpell() {
    const spellSelect = document.getElementById('spell-select');
    const spellName = spellSelect.value;
    const messageEl = document.getElementById('spell-message');

    console.log(`Intentando lanzar: ${spellName}`);
    messageEl.textContent = "Lanzando...";
    messageEl.className = 'spell-message-text';

    try {
        const response = await fetch('/hechizos/lanzar', {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                spell_name: spellName,
                incantation: `${spellName}!`
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Error al lanzar");

        messageEl.textContent = `¡Éxito! ${data.message}`;
        messageEl.classList.add('spell-success');
        fetchData();

    } catch (error) {
        console.error("Error al lanzar hechizo:", error);
        messageEl.textContent = `Error: ${error.message}`;
        messageEl.classList.add('spell-error');
        fetchData();
    }
}

// --- 5. FUNCIONES DE ACTUALIZACIÓN DE UI ---

function updateUserInfo(userData) {
    document.getElementById('user-name').innerText = userData.username;
    document.getElementById('user-role').innerText = userData.role;
    const permissionsList = document.getElementById('user-permissions');
    permissionsList.innerHTML = "";
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

function updateAuditTable(tableData) {
    const tableBody = document.getElementById('auditTable').querySelector('tbody');
    tableBody.innerHTML = "";
    if (tableData.error) {
        tableBody.innerHTML = `<tr><td colspan="4">Error al cargar logs: ${tableData.error}</td></tr>`;
        return;
    }
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

function updatePerformanceChart(chartData) {
    if (!performanceChart) return;
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

// --- 6. PUNTO DE ENTRADA PRINCIPAL ---
document.addEventListener('DOMContentLoaded', () => {

    // 1. Comprueba si el usuario está autenticado.
    const isAuthenticated = checkAuthentication();

    // 2. Si NO lo está, detén la ejecución.
    if (!isAuthenticated) {
        return;
    }

    // 3. Si SÍ lo está, INICIALIZA EL GRÁFICO
    console.log("Usuario autenticado, inicializando dashboard...");
    try {
        const ctx = document.getElementById('performanceChart').getContext('2d');
        performanceChart = new Chart(ctx, {
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
    } catch (e) {
        console.error("No se pudo inicializar el gráfico:", e);
    }

    // 4. Llama a las funciones de carga de datos
    fetchData();
    fetchUserInfo();

    // 5. Configura el 'setInterval'
    setInterval(fetchData, 5000);

    // 6. Configura los 'event listeners' de los botones
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            console.log("Cerrando sesión...");
            sessionStorage.clear();
            window.location.href = '/';
        });
    }

    const castButton = document.getElementById('cast-spell-button');
    if (castButton) {
        castButton.addEventListener('click', castSpell);
    }
});