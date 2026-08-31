const output = document.querySelector('#out');
const question = document.querySelector('#q');
const button = document.querySelector('button');

async function ask() {
  const value = question.value.trim();
  if (!value) return;
  button.disabled = true;
  output.setAttribute('aria-busy', 'true');
  output.innerHTML = '<p>Searching structure, source, and memory...</p>';
  try {
    const response = await fetch('/api/query', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({question: value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Query failed');
    output.innerHTML = `<div class="card"><div>${escapeHtml(data.answer)}</div><p class="tag">${escapeHtml(data.repository)} · commit ${escapeHtml(data.commit)} · ~${data.tokens_estimate} evidence words</p>${data.claims.map(claim => `<div class="claim">${escapeHtml(claim.confidence.toUpperCase())}: ${escapeHtml(claim.text)}</div>`).join('')}${data.caveats.length ? `<p>${escapeHtml(data.caveats.join(' '))}</p>` : ''}</div>${data.evidence.map((item, index) => `<details class="card"><summary class="tag">E${index} · ${escapeHtml(item.kind)} · ${escapeHtml(item.path)}:${item.start_line}-${item.end_line}</summary><div class="ev">${escapeHtml(item.snippet)}</div></details>`).join('')}`;
  } catch (error) {
    output.innerHTML = `<div class="card" role="alert">${escapeHtml(error.message)}. Check the repository index and try again.</div>`;
  } finally {
    button.disabled = false;
    output.setAttribute('aria-busy', 'false');
  }
}

function escapeHtml(value) {
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
}

button.addEventListener('click', ask);
question.addEventListener('keydown', event => { if (event.key === 'Enter') ask(); });

