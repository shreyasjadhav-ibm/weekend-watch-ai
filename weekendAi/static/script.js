document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    try {
        // Simulate JS error randomly
        if (Math.random() < 0.2) {
            myUndefinedFunction(); // Causes ReferenceError
        }
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        console.log(data);
    } catch (error) {
        fetch('/log-error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source: 'frontend',
                message: error.message,
                error_type: error.name
            })
        });
    }
});

