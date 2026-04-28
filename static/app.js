const form = document.getElementById('task-form');
const taskList = document.getElementById('task-list');

async function fetchTasks() {
  const res = await fetch('/api/tasks');
  const tasks = await res.json();
  renderTasks(tasks);
}

function renderTasks(tasks) {
  taskList.innerHTML = '';
  for (const task of tasks) {
    const li = document.createElement('li');

    const left = document.createElement('div');
    const title = document.createElement('div');
    title.className = `task-title ${task.status === 'done' ? 'done' : ''}`;
    title.textContent = task.title;
    const desc = document.createElement('small');
    desc.textContent = task.description || '';
    left.appendChild(title);
    left.appendChild(desc);

    const actions = document.createElement('div');
    actions.className = 'actions';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'btn-secondary';
    toggleBtn.textContent = task.status === 'done' ? 'Repasser à faire' : 'Terminer';
    toggleBtn.onclick = () => updateTask(task.id, task.status === 'done' ? 'todo' : 'done');

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

  if (!title) return;

  await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description })
  });

  form.reset();
  fetchTasks();
});

async function updateTask(id, status) {
  await fetch(`/api/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  fetchTasks();
}

async function deleteTask(id) {
  await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
  fetchTasks();
}

fetchTasks();
