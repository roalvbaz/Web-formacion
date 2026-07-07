// Definimos los usuarios con sus respectivas contraseñas personalizadas
const usuarios = [
    { centro: 'CD Zegama', user: 'aux.zegama', pass: 'MiClave123!' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },
    { centro: 'CD Alda', user: 'aux.alda', pass: 'Segura2026#' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },
    { centro: 'CD Legazpi', user: 'aux.legazpi', pass: 'Segura2026#' },

];

async function crearUsuarios() {
    console.log("Iniciando creación de usuarios...");
    
    for (const item of usuarios) {
        const formData = new FormData();
        formData.append('username', item.user);
        formData.append('password', item.pass);
        formData.append('password_confirm', item.pass);
        formData.append('role', 'user');

        try {
            const response = await fetch('/admin/register', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok || response.redirected) {
                console.log(`✅ Creado: ${item.user} | Password: ${item.pass}`);
            } else {
                console.error(`❌ Error al crear: ${item.user}`);
            }
        } catch (e) {
            console.error(`⚠️ Fallo de conexión para ${item.user}:`, e);
        }
    }
    console.log("--- Proceso finalizado ---");
}

crearUsuarios();