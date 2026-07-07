function getFilterParams() {
  const dni = document.getElementById('filter-dni').value.trim();
  const email = document.getElementById('filter-email').value.trim();
  const centro = document.getElementById('filter-centro').value.trim();
  const aprobado = document.getElementById('filter-aprobado').value;
  const params = new URLSearchParams();
  if (dni) params.set('dni', dni);
  if (email) params.set('email', email);
  if (centro) params.set('centro', centro);
  if (aprobado !== '') params.set('aprobado', aprobado);
  return params;
}

function updateExportLink() {
  const params = getFilterParams();
  const exportLink = document.querySelector('a[href^="/api/export/csv"]');
  exportLink.href = '/api/export/csv' + (params.toString() ? `?${params.toString()}` : '');
}

async function loadAdminData() {
  const params = getFilterParams();
  const response = await fetch('/api/admin/registros' + (params.toString() ? `?${params.toString()}` : ''));
  const data = await response.json();
  const rows = document.getElementById('rows');
  const emptyMessage = document.getElementById('admin-message');
  const totalRecords = document.getElementById('total-records');
  const approvedRecords = document.getElementById('approved-records');
  const failedRecords = document.getElementById('failed-records');

  rows.innerHTML = '';
  if (!data.length) {
    emptyMessage.hidden = false;
    emptyMessage.textContent = 'No hay registros que coincidan con el filtro seleccionado.';
    emptyMessage.style.background = '#fef3c7';
    emptyMessage.style.color = '#92400e';
    emptyMessage.style.border = '1px solid #fcd34d';
    totalRecords.textContent = '0';
    approvedRecords.textContent = '0';
    failedRecords.textContent = '0';
    return;
  }

  emptyMessage.hidden = true;
  let approvedCount = 0;
  data.forEach(item => {
    const tr = document.createElement('tr');
    const approvedBadge = item.aprobado ? '<span class="badge yes">Sí</span>' : '<span class="badge no">No</span>';
    const respuestas = JSON.stringify(item.respuestas, null, 0);
    tr.innerHTML = `
      <td>${item.id}</td>
      <td>${item.nombre}</td>
      <td>${item.dni}</td>
      <td>${item.email}</td>
      <td>${item.centro || ''}</td>
      <td>${item.score}</td>
      <td>${approvedBadge}</td>
      <td>${new Date(item.fecha).toLocaleString('es-ES')}</td>
      <td><pre>${respuestas}</pre></td>
      <td><button class="delete-button" onclick="deleteRegistro(${item.id})">Eliminar</button></td>
    `;
    rows.appendChild(tr);
    if (item.aprobado) approvedCount += 1;
  });

  totalRecords.textContent = data.length;
  approvedRecords.textContent = approvedCount;
  failedRecords.textContent = data.length - approvedCount;
}

async function deleteRegistro(id) {
  if (!confirm('¿Eliminar este registro? Esta acción no se puede deshacer.')) {
    return;
  }
  const response = await fetch(`/api/admin/registros/${id}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' }
  });
  const result = await response.json();
  const messageBox = document.getElementById('admin-message');
  messageBox.hidden = false;
  if (response.ok && result.ok) {
    messageBox.textContent = result.message;
    messageBox.style.background = '#ecfdf5';
    messageBox.style.color = '#065f46';
    messageBox.style.border = '1px solid #a7f3d0';
    loadAdminData();
  } else {
    messageBox.textContent = result.error || 'No se pudo eliminar el registro.';
    messageBox.style.background = '#fef2f2';
    messageBox.style.color = '#b91c1c';
    messageBox.style.border = '1px solid #fecaca';
  }
}

document.getElementById('filter-apply').addEventListener('click', () => {
  updateExportLink();
  loadAdminData();
});

document.getElementById('filter-clear').addEventListener('click', () => {
  document.getElementById('filter-dni').value = '';
  document.getElementById('filter-email').value = '';
  document.getElementById('filter-aprobado').value = '';
  updateExportLink();
  loadAdminData();
});

updateExportLink();
loadAdminData();
