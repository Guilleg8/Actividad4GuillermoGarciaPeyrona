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
        // 1. Llama al backend para validar el usuario
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error desconocido");
        }

        // 2. El backend da el OK y devuelve los datos del usuario
        const userData = await response.json(); // {username: "...", role: "..."}

        console.log(`Login OK. Guardando en sessionStorage: ${userData.username}, ${userData.role}`);

        // 3. ¡IMPORTANTE! Guarda los datos en sessionStorage
        sessionStorage.setItem('magic_user_username', userData.username);
        sessionStorage.setItem('magic_user_role', userData.role);

        // 4. Redirige al dashboard
        window.location.href = '/dashboard';

    } catch (error) {
        console.error("Error en el login:", error);
        errorText.textContent = error.message;
    }
});