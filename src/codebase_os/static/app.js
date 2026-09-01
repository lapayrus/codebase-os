const repositorySelect = document.querySelector('#repository-select');
const repositoryCount = document.querySelector('#repository-count');
const deleteButton = document.querySelector('#delete-repository');
const indexForm = document.querySelector('#index-form');
const indexStatus = document.querySelector('#index-status');
const queryForm = document.querySelector('#query-form');
const question = document.querySelector('#q');
const askButton = document.querySelector('#ask-button');
const answerRegion = document.querySelector('#answer-region');
const sessionStatus = document.querySelector('#session-status');
const railRepository = document.querySelector('#rail-repository');
const railCommit = document.querySelector('#rail-commit');
const memoryStatus = document.querySelector('#memory-status');
let repositories = [];

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (response.status === 401 || response.status === 403) {
    sessionStatus.innerHTML = '<span class="status-dot error" aria-hidden="true"></span><span>Permission denied</span>';
    throw new Error('Permission denied');
  }
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

function selectedRepository() { return repositories.find(item => item.name === repositorySelect.value); }
function setSession(active) { sessionStatus.innerHTML = `<span class="status-dot${active ? '' : ' error'}" aria-hidden="true"></span><span>${active ? 'Session active' : 'Session unavailable'}</span>`; }

async function loadRepositories() {
  repositoryCount.textContent = 'Loading repositories';
  try {
    repositories = await request('/api/repositories');
    repositorySelect.innerHTML = '';
    if (!repositories.length) {
      repositorySelect.add(new Option('No repositories indexed', ''));
      repositoryCount.textContent = 'No repositories indexed';
      repositorySelect.disabled = true;
      deleteButton.disabled = true;
      setSession(true);
      return;
    }
    repositories.forEach(item => repositorySelect.add(new Option(item.name, item.name)));
    repositorySelect.disabled = false;
    repositoryCount.textContent = `${repositories.length} source${repositories.length === 1 ? '' : 's'} ready`;
    setSession(true);
    selectRepository();
  } catch (error) {
    repositorySelect.innerHTML = '<option>Unable to load repositories</option>';
    repositoryCount.textContent = error.message;
  }
}

async function selectRepository() {
  const repository = selectedRepository();
  deleteButton.disabled = !repository;
  railRepository.textContent = repository ? repository.name : 'No repository selected';
  railCommit.textContent = repository ? `commit ${repository.commit || 'pending'}` : '—';
  memoryStatus.textContent = repository ? 'Loading team context…' : 'Select a repository to load team context.';
  if (!repository) return;
  try {
    const memories = await request(`/api/memories/${encodeURIComponent(repository.name)}`);
    memoryStatus.textContent = memories.length ? `${memories.length} memory${memories.length === 1 ? '' : 'ies'} available.` : 'No memories stored yet.';
  } catch (error) { memoryStatus.textContent = error.message; }
}

function renderAnswer(data) {
  const claims = (data.claims || []).map(claim => `<li><span class="confidence ${escapeHtml(claim.confidence)}">${escapeHtml(claim.confidence)}</span>${escapeHtml(claim.text)}</li>`).join('');
  const evidence = (data.evidence || []).map((item, index) => `<details class="evidence-item"><summary><span>E${index + 1}</span>${escapeHtml(item.path)}:${item.start_line}-${item.end_line}</summary><div class="code-snippet">${escapeHtml(item.snippet)}</div></details>`).join('');
  const caveats = (data.caveats || []).map(caveat => `<li>${escapeHtml(caveat)}</li>`).join('');
  answerRegion.innerHTML = `<article class="answer panel"><div class="answer-meta"><span class="eyebrow">ANSWER / ${escapeHtml(data.model || 'LOCAL')}</span><span class="mono">${escapeHtml(data.repository)} · ${escapeHtml(data.commit)}</span></div><p class="answer-text">${escapeHtml(data.answer)}</p><div class="answer-columns"><section><h3>Claims</h3><ul class="claims">${claims || '<li>No supported claims found.</li>'}</ul>${caveats ? `<h3>Caveats</h3><ul class="caveats">${caveats}</ul>` : ''}</section><section><h3>Source spans <span class="muted">${data.evidence?.length || 0}</span></h3>${evidence || '<p class="muted">No evidence spans returned.</p>'}</section></div></article>`;
}

async function ask(event) {
  event.preventDefault();
  if (!question.value.trim()) return;
  askButton.disabled = true;
  answerRegion.setAttribute('aria-busy', 'true');
  answerRegion.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span><p>Searching structure, source, and memory…</p></div>';
  try {
    const repository = selectedRepository();
    renderAnswer(await request('/api/query', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({question: question.value.trim(), repository: repository?.name})}));
  } catch (error) {
    answerRegion.innerHTML = `<div class="error-state" role="alert"><span class="empty-glyph" aria-hidden="true">!</span><h2>${escapeHtml(error.message)}</h2><p>Check your session and repository index, then try again.</p></div>`;
  } finally {
    askButton.disabled = false;
    answerRegion.setAttribute('aria-busy', 'false');
  }
}

async function indexRepository(event) {
  event.preventDefault();
  indexStatus.textContent = 'Indexing repository…';
  const body = new URLSearchParams(new FormData(indexForm));
  try {
    await request(`/api/repositories/index?${body.toString()}`, {method: 'POST'});
    indexStatus.textContent = 'Repository indexed.';
    await loadRepositories();
  } catch (error) { indexStatus.textContent = error.message; }
}

async function deleteRepository() {
  const repository = selectedRepository();
  if (!repository || !window.confirm(`Delete ${repository.name} and its indexed snapshot?`)) return;
  deleteButton.disabled = true;
  try {
    await request(`/api/repositories/${encodeURIComponent(repository.name)}`, {method: 'DELETE'});
    await loadRepositories();
  } catch (error) { repositoryCount.textContent = error.message; deleteButton.disabled = false; }
}

function escapeHtml(value) { return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;'); }
repositorySelect.addEventListener('change', selectRepository);
queryForm.addEventListener('submit', ask);
indexForm.addEventListener('submit', indexRepository);
deleteButton.addEventListener('click', deleteRepository);
loadRepositories();
