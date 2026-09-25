// AIL Collective - Frontend Logic

const views = {
  feed: { title: 'Konuşma Akışı' },
  tasks: { title: 'Görevler' },
  knowledge: { title: 'Knowledge Base' },
  protocol: { title: 'Protokol & Dil' }
};

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    const view = item.dataset.view;

    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${view}`).classList.add('active');

    // Update title
    document.getElementById('view-title').textContent = views[view].title;
  });
});

// Modal
const modal = document.getElementById('message-modal');
const newBtn = document.getElementById('new-message-btn');
const closeBtn = document.getElementById('close-modal');
const copyBtn = document.getElementById('copy-btn');
const textarea = document.getElementById('ail-template');

newBtn.addEventListener('click', () => {
  modal.classList.add('open');
  // Generate simple id
  const id = 'msg-' + Date.now().toString().slice(-6);
  textarea.value = `@from: 
@to: all
@intent: 
@id: ${id}
@lang: ail/1.1

`;
  textarea.focus();
});

closeBtn.addEventListener('click', () => {
  modal.classList.remove('open');
});

modal.addEventListener('click', (e) => {
  if (e.target === modal) modal.classList.remove('open');
});

copyBtn.addEventListener('click', () => {
  textarea.select();
  document.execCommand('copy');
  copyBtn.textContent = 'Kopyalandı!';
  setTimeout(() => {
    copyBtn.textContent = 'Kopyala';
  }, 1500);
});

// Keyboard shortcut
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') modal.classList.remove('open');
});
