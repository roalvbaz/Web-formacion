async function loadUsers() {
  const response = await fetch('/api/admin/users');
  const users = await response.json();
  const rows = document.getElementById('user-rows');
  const messageBox = document.getElementById('user-message');

  rows.innerHTML = '';
  if (!users.length) {
    messageBox.hidden = false;
    messageBox.textContent = 'No hay usuarios registrados.';
    messageBox.style.background = '#fef3c7';
    messageBox.style.color = '#92400e';
    messageBox.style.border = '1px solid #fcd34d';
    return;
  }

  messageBox.hidden = true;
  users.forEach(user => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${user.id}</td>
      <td>${user.username}</td>
      <td>${user.role}</td>
      <td>${new Date(user.created_at).toLocaleString('es-ES')}</td>
      <td>
        <button class="delete-button" onclick="deleteUser(${user.id}, '${user.username}')">Eliminar</button>
      </td>
    `;
    rows.appendChild(tr);
  });
}

async function deleteUser(id, username) {
  if (!confirm(`¿Eliminar al usuario ${username}? Esta acción no se puede deshacer.`)) {
    return;
  }

  const response = await fetch(`/api/admin/users/${id}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' }
  });
  const result = await response.json();
  const messageBox = document.getElementById('user-message');
  messageBox.hidden = false;

  if (response.ok && result.ok) {
    messageBox.textContent = result.message;
    messageBox.style.background = '#ecfdf5';
    messageBox.style.color = '#065f46';
    messageBox.style.border = '1px solid #a7f3d0';
    loadUsers();
  } else {
    messageBox.textContent = result.error || 'No se pudo eliminar el usuario.';
    messageBox.style.background = '#fef2f2';
    messageBox.style.color = '#b91c1c';
    messageBox.style.border = '1px solid #fecaca';
  }
}

loadUsers();
