// app/frontend/login.js

document.getElementById('login-button').addEventListener('click', async () => {
    const usernameInput = document.getElementById('username-input');
    const username = usernameInput.value;
    const errorText = document.getElementById('login-error');

    if (!username) {
        errorText.textContent = "Por favor, introduzca un nombre de usuario.";
        return;
    }

    errorText.textContent = ""; // Limpiar errores previos

    try {
        // --- ¡Llama al nuevo endpoint del backend! ---
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username }) // Envía el username
        });

        if (!response.ok) {
            // Si es 404 (No Encontrado) u otro error
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error desconocido");
        }

        // --- Éxito ---
        const userData = await response.json(); // Recibe {username: "...", role: "..."}

        console.log(`Iniciando sesión como: ${userData.username} (Rol: ${userData.role})`);

        // Guarda la identidad validada en el navegador
        localStorage.setItem('magic_user_username', userData.username);
        localStorage.setItem('magic_user_role', userData.role);

        // Redirige al dashboard principal
        window.location.href = '/dashboard';


    } catch (error) {
        console.error("Error en el login:", error);
        errorText.textContent = error.message;
    }
});