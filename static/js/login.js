document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    const err = document.getElementById('error-msg');
    
    try {
        // Use relative path for production routing
        const apiUrl = '/api/login';

        const formData = new URLSearchParams();
        formData.append('username', u);
        formData.append('password', p);

        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('nemesis_token', data.access_token);
            err.classList.add('hidden');
            window.location.href = '/admin.html';
        } else {
            err.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${data.detail || 'Access Denied.'}`;
            err.classList.remove('hidden');
        }
    } catch (error) {
        err.innerHTML = '<i class="fa-solid fa-link-slash"></i> Connection to mainframe failed.';
        err.classList.remove('hidden');
    }
});
