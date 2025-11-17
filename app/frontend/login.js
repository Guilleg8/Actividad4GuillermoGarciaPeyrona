document.getElementById('login-button').addEventListener('click', async () => {
    const usernameInput = document.getElementById('username-input');
    const username = usernameInput.value;
    const errorText = document.getElementById('login-error');

    if (!username) {
        errorText.textContent = "Por favor, introduzca un nombre de usuario.";
        return;
    }

    errorText.textContent = "";

    try {
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

        const userData = await response.json(); // {username: "...", role: "..."}

        console.log(`Login OK. Guardando en sessionStorage: ${userData.username}, ${userData.role}`);

        sessionStorage.setItem('magic_user_username', userData.username);
        sessionStorage.setItem('magic_user_role', userData.role);

        window.location.href = '/dashboard';

    } catch (error) {
        console.error("Error en el login:", error);
        errorText.textContent = error.message;
    }
});