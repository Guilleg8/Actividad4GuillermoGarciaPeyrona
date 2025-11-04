// app.js

// Dirección de nuestra API de FastAPI
const API_URL = "http://127.0.0.1:8000/api/dashboard-data";

// --- 1. Inicialización de Mermaid (Diagrama) ---
// (Mermaid se inicializa automáticamente al cargar la página)
mermaid.initialize({
    startOnLoad: true,
    theme: 'base', // Usamos un tema 'base' porque 'dark' es de pago
    themeVariables: {
        background: '#f0f0f0',
        primaryColor: '#2a2a4e',
        nodeBorder: '#2a2a4e',
        lineColor: '#3a3a6e',
        textColor: '#1a1a2e'
    }
});


// --- 2. Inicialización del Gráfico (Chart.js) ---
const ctx = document.getElementById('performanceChart').getContext('2d');
const performanceChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // Se llenará con el tiempo
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
            yLatency: {
                type: 'linear',
                position: 'left',
                ticks: { color: '#e0e0e0' },
                grid: { color: '#4a4a7c' }
            },
            yEvents: {
                type: 'linear',
                position: 'right',
                ticks: { color: '#e0e0e0' },
                grid: { color: 'transparent' }
            },
            x: {
                ticks: { color: '#e0e0e0' },
                grid: { color: '#4a4a7c' }
            }
        },
        plugins: {
            legend: {
                labels: { color: '#e0e0e0' }
            }
        }
    }
});


// --- 3. Funciones de Actualización ---

/**
 * Actualiza la tabla de auditoría con nuevos datos.
 */
function updateAuditTable(tableData) {
    const tableBody = document.getElementById('auditTable').querySelector('tbody');
    tableBody.innerHTML = ""; // Limpiar tabla

    // Si hay un error del backend
    if (tableData.error) {
        tableBody.innerHTML = `<tr><td colspan="4">Error al cargar logs: ${tableData.error}</td></tr>`;
        return;
    }

    // Llenar la tabla
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
    const now = new Date();
    const timeLabel = now.toLocaleTimeString();

    const chart = performanceChart.data;

    // Añadir nuevos datos
    chart.labels.push(timeLabel);
    chart.datasets[0].data.push(chartData.current_latency_ms); // Latencia
    chart.datasets[1].data.push(chartData.events_per_second); // Eventos

    // Limitar el gráfico a 10 puntos de datos para que se mueva
    const maxDataPoints = 10;
    if (chart.labels.length > maxDataPoints) {
        chart.labels.shift();
        chart.datasets[0].data.shift();
        chart.datasets[1].data.shift();
    }

    // Actualizar el gráfico y los resúmenes
    performanceChart.update();
    document.getElementById('metric-latency').innerText = chartData.current_latency_ms;
    document.getElementById('metric-events').innerText = chartData.events_per_second;
}

/**
 * Función principal para obtener datos de la API.
 */
async function fetchData() {
    console.log("Llamando a la API de FastAPI...");
    try {
        const response = await fetch(API_URL);
        if (!response.ok) {
            throw new Error(`Error de red: ${response.statusText}`);
        }

        const data = await response.json();

        // Actualizar los componentes visuales
        updateAuditTable(data.table);
        updatePerformanceChart(data.chart);

    } catch (error) {
        console.error("Error al obtener datos del dashboard:", error);
        // Podríamos mostrar un error en la UI
    }
}


// --- 4. Ejecución ---

// Esperar a que el DOM esté cargado
document.addEventListener('DOMContentLoaded', () => {
    // Llamar a la API inmediatamente al cargar
    fetchData();

    // Configurar la actualización en "tiempo real" (polling)
    // Llama a la API cada 5 segundos
    setInterval(fetchData, 5000);
});