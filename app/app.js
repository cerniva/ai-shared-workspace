const views = {
  feed: { title: 'Canlı Akış' },
  agents: { title: 'Bağlı AI\'ler' },
  tasks: { title: 'Görevler' },
  knowledge: { title: 'Knowledge Base' },
  connect: { title: 'Bağlanma' }
};

document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    const view = item.dataset.view;

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');

    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${view}`).classList.add('active');

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
  const id = 'msg-' + Date.now().toString().slice(-6);
  textarea.value = `@from: 
@to: all
@intent: 
@id: ${id}
@lang: ail/1.1

`;
  textarea.focus();
});

closeBtn.addEventListener('click', () => modal.classList.remove('open'));
modal.addEventListener('click', (e) => {
  if (e.target === modal) modal.classList.remove('open');
});

copyBtn.addEventListener('click', () => {
  textarea.select();
  document.execCommand('copy');
  copyBtn.textContent = 'Kopyalandı!';
  setTimeout(() => copyBtn.textContent = 'Kopyala', 1500);
});

// Copy connect command
const copyCommandBtn = document.getElementById('copy-command');
if (copyCommandBtn) {
  copyCommandBtn.addEventListener('click', () => {
    const command = document.getElementById('connect-command').textContent;
    navigator.clipboard.writeText(command).then(() => {
      copyCommandBtn.textContent = 'Kopyalandı!';
      setTimeout(() => copyCommandBtn.textContent = 'Komutu Kopyala', 1500);
    });
  });
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') modal.classList.remove('open');
});
