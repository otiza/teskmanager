const form = document.getElementById('task-form');
const taskList = document.getElementById('task-list');

function isOverdue(task) {
  if (!task.deadline || task.status === 'done') return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return new Date(`${task.deadline}T00:00:00`) < today;
}

function formatDeadline(deadline) {
  if (!deadline) return 'Pas de date limite';
  return new Date(`${deadline}T00:00:00`).toLocaleDateString('fr-FR');
}

async function fetchTasks() {
  const res = await fetch('/api/tasks');
  const tasks = await res.json();
  renderTasks(tasks);
}

function renderTasks(tasks) {
  taskList.innerHTML = '';
  for (const task of tasks) {
    const li = document.createElement('li');
    if (isOverdue(task)) li.classList.add('overdue');

    const left = document.createElement('div');
    left.className = 'task-content';

    const title = document.createElement('div');
    title.className = `task-title ${task.status === 'done' ? 'done' : ''}`;
    title.textContent = task.title;

    const desc = document.createElement('small');
    desc.className = 'task-description';
    desc.textContent = task.description || '—';

    const meta = document.createElement('div');
    meta.className = 'task-meta';
    const assignedTo = task.assigned_to ? task.assigned_to : 'Non assignée';
    meta.innerHTML = `
      <span>👤 ${assignedTo}</span>
      <span>📅 ${formatDeadline(task.deadline)}</span>
      <span class="badge ${task.status}">${task.status === 'done' ? 'Terminée' : 'À faire'}</span>
    `;

    left.append(title, desc, meta);

    const actions = document.createElement('div');
    actions.className = 'actions';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'btn-secondary';
    toggleBtn.textContent = task.status === 'done' ? 'Réactiver' : 'Terminer';
    toggleBtn.onclick = () => updateTask(task.id, { status: task.status === 'done' ? 'todo' : 'done' });

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn-danger';
    deleteBtn.textContent = 'Supprimer';
    deleteBtn.onclick = () => deleteTask(task.id);

    actions.append(toggleBtn, deleteBtn);
    li.append(left, actions);
    taskList.appendChild(li);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const title = document.getElementById('title').value.trim();
  const description = document.getElementById('description').value.trim();
  const assigned_to = document.getElementById('assigned_to').value.trim();
  const deadline = document.getElementById('deadline').value;

  if (!title) return;

  const res = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, assigned_to, deadline })
  });

  if (!res.ok) {
    const data = await res.json();
    alert(data.error || 'Erreur lors de la création de la tâche.');
    return;
  }

  form.reset();
  fetchTasks();
});

async function updateTask(id, payload) {
  await fetch(`/api/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  fetchTasks();
}

async function deleteTask(id) {
  await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
  fetchTasks();
}

fetchTasks();
