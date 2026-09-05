const domain = document.querySelector('#domain');
const errorBox = document.querySelector('#error');
const results = document.querySelector('#results');
const statusBadge = document.querySelector('#service-status');
let models = {};
let latest = null;

document.querySelectorAll('.tab').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach((item) => {
    const selected = item === button;
    item.classList.toggle('active', selected);
    item.setAttribute('aria-selected', String(selected));
  });
  document.querySelector('#single-form').classList.toggle('hidden', button.dataset.tab !== 'single');
  document.querySelector('#fasta-form').classList.toggle('hidden', button.dataset.tab !== 'fasta');
  hideError();
}));

fetch('/api/models').then((response) => {
  if (!response.ok) throw new Error('Model service is unavailable.');
  return response.json();
}).then((data) => {
  models = Object.fromEntries(data.models.map((item) => [item.model_group, item]));
  const available = data.models.filter((item) => item.available).length;
  statusBadge.textContent = `${available}/${data.models.length} models ready`;
  statusBadge.classList.toggle('warning', available !== data.models.length);
  updateModelMeta();
}).catch((error) => {
  statusBadge.textContent = 'Models unavailable';
  statusBadge.classList.add('warning');
  document.querySelector('#model-meta').textContent = error.message;
});

domain.addEventListener('change', updateModelMeta);
function updateModelMeta() {
  const item = models[domain.value];
  document.querySelector('#model-meta').textContent = item?.available
    ? `${item.organism.replace('_unspecified', '')} · ${item.model.replaceAll('_', ' ')} · maximum ${item.maximum_length} nt`
    : 'Model unavailable';
}

const sequence = document.querySelector('#sequence');
sequence.addEventListener('input', () => document.querySelector('#sequence-length').textContent = `${sequence.value.replace(/\s/g, '').length} nt`);
const fileInput = document.querySelector('#fasta-file');
fileInput.addEventListener('change', () => document.querySelector('#file-name').textContent = fileInput.files[0]?.name || 'Choose a FASTA file');

document.querySelector('#single-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await submit(event.currentTarget, () => fetch('/api/predict/sequence', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({model_group: domain.value, sequence: sequence.value})}));
});
document.querySelector('#fasta-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!fileInput.files[0]) return showError('Choose a FASTA file first.');
  const body = new FormData(); body.append('model_group', domain.value); body.append('file', fileInput.files[0]);
  await submit(event.currentTarget, () => fetch('/api/predict/fasta', {method: 'POST', body}));
});

async function submit(form, request) {
  hideError(); results.classList.add('hidden');
  const button = form.querySelector('.primary'), original = button.textContent;
  button.disabled = true; button.textContent = 'Predicting…';
  try {
    const response = await request(), data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Prediction failed.');
    render(data);
  } catch (error) { showError(error.message || 'Prediction failed.'); }
  finally { button.disabled = false; button.textContent = original; }
}
function showError(message) { errorBox.textContent = message; errorBox.classList.remove('hidden'); }
function hideError() { errorBox.classList.add('hidden'); errorBox.textContent = ''; }

function render(data) {
  latest = data;
  document.querySelector('#result-title').textContent = data.total === 1 ? 'Sequence prediction' : `${data.total.toLocaleString()} sequences analyzed`;
  document.querySelector('#result-meta').textContent = `${data.organism.replace('_unspecified', '')} · ${data.model.replaceAll('_', ' ')} · threshold ${format(data.threshold)}`;
  const notice = document.querySelector('#result-notice'); notice.textContent = data.message || ''; notice.classList.toggle('hidden', !data.message);
  document.querySelector('#promoter-count').textContent = data.summary.promoter.toLocaleString();
  document.querySelector('#non-promoter-count').textContent = data.summary.non_promoter.toLocaleString();
  renderChart(data.summary.promoter, data.summary.non_promoter);
  document.querySelector('#result-rows').innerHTML = data.predictions.map((row) => {
    const promoter = row.predicted_class === 'promoter';
    return `<tr><td title="${escapeHtml(row.sequence_id)}">${escapeHtml(row.sequence_id)}</td><td>${row.length} nt</td><td><span class="badge ${promoter ? '' : 'negative'}">${promoter ? 'Promoter' : 'Not Promoter'}</span></td><td><div class="probability"><div class="bar"><i style="width:${row.promoter_probability * 100}%"></i></div>${format(row.promoter_probability)}</div></td></tr>`;
  }).join('');
  results.classList.remove('hidden'); results.scrollIntoView({behavior: 'smooth', block: 'start'});
}

function renderChart(promoter, notPromoter) {
  if (!window.Plotly) { document.querySelector('#pie-chart').textContent = `Promoter: ${promoter} · Not Promoter: ${notPromoter}`; return; }
  Plotly.react('pie-chart', [{values: [promoter, notPromoter], labels: ['Promoter', 'Not Promoter'], type: 'pie', hole: .58, sort: false, direction: 'clockwise', domain: {x: [.08, .92], y: [.08, .92]}, marker: {colors: ['#0a7180', '#d4a72c'], line: {color: '#fff', width: 3}}, textinfo: 'label+percent', textposition: 'inside', insidetextorientation: 'horizontal', hovertemplate: '%{label}<br>%{value:,} sequence(s)<br>%{percent}<extra></extra>'}], {autosize: true, margin: {t: 8, r: 8, b: 8, l: 8}, height: 280, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', showlegend: false, uniformtext: {minsize: 11, mode: 'hide'}, annotations: [{text: `<b>${(promoter + notPromoter).toLocaleString()}</b><br><span style="font-size:12px">TOTAL</span>`, showarrow: false, font: {size: 22, color: '#102f48'}}]}, {responsive: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d']});
}
function format(value) { return `${(value * 100).toFixed(1)}%`; }
function escapeHtml(value) { const div = document.createElement('div'); div.textContent = value; return div.innerHTML; }

document.querySelector('#download').addEventListener('click', () => {
  if (!latest) return;
  const quote = (value) => `"${String(value).replaceAll('"', '""')}"`;
  const lines = [['sequence_id', 'length', 'classification', 'promoter_probability'], ...latest.predictions.map((row) => [row.sequence_id, row.length, row.predicted_class === 'promoter' ? 'Promoter' : 'Not Promoter', row.promoter_probability])];
  const blob = new Blob([lines.map((row) => row.map(quote).join(',')).join('\n')], {type: 'text/csv'}), link = document.createElement('a');
  link.href = URL.createObjectURL(blob); link.download = `${latest.model_group}_predictions.csv`; link.click(); URL.revokeObjectURL(link.href);
});
