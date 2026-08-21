const palette = { Script: '#6fa9ff', LocalScript: '#62c5eb', ModuleScript: '#9b8cff', RemoteEvent: '#f5a66b', RemoteFunction: '#f2bc6f', Service: '#54d6ba', DataStore: '#e889cc', OrderedDataStore: '#e889cc', CollectionServiceTag: '#d6d06f', Attribute: '#e887a1', Folder: '#93a4c0', Model: '#88b9a1', Place: '#ffffff', RobloxInstance: '#93a4c0' };
let cy; let graphData = { nodes: [], edges: [] }; let activeTypes = new Set(); let activeEdges = new Set();
const el = (id) => document.getElementById(id);

async function api(path) { const response = await fetch(path); if (!response.ok) throw new Error(await response.text()); return response.json(); }
function escape(value) { return String(value ?? '').replace(/[&<>"']/g, (letter) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' }[letter])); }
function setEmpty(visible, message) { const state = el('empty-state'); state.classList.toggle('is-hidden', !visible); if (message) state.querySelector('p').textContent = message; }

function populateFilters() {
  const types = [...new Set(graphData.nodes.map((node) => node.type))].sort(); const edges = [...new Set(graphData.edges.map((edge) => edge.type))].sort();
  activeTypes = new Set(types); activeEdges = new Set(edges);
  buildFilters('node-filters', types, activeTypes, 'type'); buildFilters('edge-filters', edges, activeEdges, 'edge');
}
function buildFilters(containerId, values, active, kind) {
  const container = el(containerId); container.replaceChildren();
  values.forEach((value) => { const label = document.createElement('label'); label.className = 'filter'; label.innerHTML = `<input checked type="checkbox"><i style="--filter-color:${palette[value] || '#91a0b9'}"></i>${escape(value)}`; label.querySelector('input').addEventListener('change', (event) => { event.target.checked ? active.add(value) : active.delete(value); applyFilters(); }); container.append(label); });
}
function applyFilters() {
  if (!cy) return; const visibleNodes = cy.nodes().filter((node) => activeTypes.has(node.data('type'))); cy.elements().hide(); visibleNodes.show(); visibleNodes.connectedEdges().filter((edge) => activeEdges.has(edge.data('type')) && edge.source().visible() && edge.target().visible()).show();
}
function makeGraph() {
  const elements = [
    ...graphData.nodes.map((node) => ({ data: { ...node, label: node.name, color: palette[node.type] || '#91a0b9' } })),
    ...graphData.edges.map((edge) => ({ data: { ...edge, source: edge.source_id, target: edge.target_id } })),
  ];
  if (cy) cy.destroy();
  cy = cytoscape({ container: el('cy'), elements, wheelSensitivity: .18, style: [
    { selector: 'node', style: { 'background-color':'data(color)', label:'data(label)', color:'#dbe6fb', 'font-size':9, 'text-valign':'bottom', 'text-margin-y':5, width: 'mapData(degree, 0, 20, 18, 38)', height: 'mapData(degree, 0, 20, 18, 38)', 'border-width':1, 'border-color':'#b9c6de55', 'overlay-opacity':0 } },
    { selector: 'node[type = "ModuleScript"]', style: { shape:'round-rectangle' } }, { selector: 'node[type = "RemoteEvent"], node[type = "RemoteFunction"]', style: { shape:'diamond' } }, { selector: 'node[type = "Service"]', style: { shape:'hexagon' } },
    { selector: 'edge', style: { width:1, 'line-color':'#536583', 'target-arrow-color':'#536583', 'target-arrow-shape':'triangle', 'curve-style':'bezier', opacity:.62 } },
    { selector: '.focused', style: { 'border-width':3, 'border-color':'#ffffff', 'z-index':9 } }, { selector: '.neighbour', style: { 'border-width':2, 'border-color':'#aebdff', opacity:1 } }, { selector: '.faded', style: { opacity:.11 } }, { selector: '.selected-edge', style: { width:2.5, 'line-color':'#aebdff', 'target-arrow-color':'#aebdff', opacity:1 } },
  ], layout: { name:'cose', animate:false, idealEdgeLength:100, nodeRepulsion:6000, gravity:.14, padding:46 } });
  cy.nodes().forEach((node) => node.data('degree', node.degree()));
  cy.on('tap', 'node', (event) => focusNode(event.target)); cy.on('mouseover', 'node', (event) => highlight(event.target)); cy.on('mouseout', 'node', () => clearHighlight()); cy.on('tap', (event) => { if (event.target === cy) { clearHighlight(); el('detail-panel').classList.add('is-hidden'); } });
}
function highlight(node) { cy.elements().addClass('faded'); node.removeClass('faded').addClass('focused'); node.neighborhood().removeClass('faded').addClass('neighbour'); node.connectedEdges().addClass('selected-edge'); }
function clearHighlight() { cy.elements().removeClass('faded focused neighbour selected-edge'); }
function focusNode(node) {
  highlight(node); cy.animate({ center:{ eles:node }, zoom:Math.max(cy.zoom(), 1.2) }, { duration:250 }); const data = node.data(); const incoming = node.incomers('edge'); const outgoing = node.outgoers('edge');
  el('detail-type').textContent = data.type; el('detail-name').textContent = data.name; el('detail-path').textContent = data.path || 'No path'; el('incoming-count').textContent = incoming.length; el('outgoing-count').textContent = outgoing.length;
  const relationships = [...incoming, ...outgoing].slice(0, 20).map((edge) => { const other = edge.source().id() === node.id() ? edge.target() : edge.source(); return `<li><small>${escape(edge.data('type'))}</small>${escape(other.data('name'))}</li>`; }).join(''); el('relationships').innerHTML = relationships || '<li>No direct relationships</li>';
  const source = data.source || ''; el('source-section').style.display = source ? 'block' : 'none'; el('source-preview').textContent = source.slice(0, 1400); el('detail-panel').classList.remove('is-hidden');
}
function runLayout() { if (!cy) return; const name = el('layout-select').value; cy.layout({ name, animate:true, animationDuration:350, padding:45, spacingFactor:1.1, avoidOverlap:true, directed:true, roots: cy.nodes().filter((node) => node.data('type') === 'Place') }).run(); }
async function search() { const query = el('search-input').value.trim(); const projectId = el('project-select').value; if (!query || !projectId) return; const data = await api(`/api/search?project_id=${encodeURIComponent(projectId)}&query=${encodeURIComponent(query)}`); if (data.results[0] && cy) focusNode(cy.getElementById(data.results[0].id)); }
async function loadProject(projectId) { if (!projectId) { setEmpty(true); return; } const data = await api(`/api/graph?project_id=${encodeURIComponent(projectId)}`); graphData = data; setEmpty(!data.nodes.length, data.nodes.length ? '' : 'This project has no architectural nodes yet.'); populateFilters(); makeGraph(); el('graph-stats').textContent = `${data.nodes.length.toLocaleString()} nodes · ${data.edges.length.toLocaleString()} edges`; }
async function init() { try { const { projects } = await api('/api/projects'); const select = el('project-select'); projects.forEach((project) => { const option = document.createElement('option'); option.value = project.id; option.textContent = project.name; select.append(option); }); select.addEventListener('change', () => loadProject(select.value)); el('search-input').addEventListener('keydown', (event) => { if (event.key === 'Enter') search(); }); el('fit-button').addEventListener('click', () => cy?.fit(undefined, 42)); el('close-panel').addEventListener('click', () => { el('detail-panel').classList.add('is-hidden'); clearHighlight(); }); el('layout-select').addEventListener('change', runLayout); el('all-types').addEventListener('click', () => { activeTypes = new Set(graphData.nodes.map((node) => node.type)); document.querySelectorAll('#node-filters input').forEach((input) => input.checked = true); applyFilters(); }); el('all-edges').addEventListener('click', () => { activeEdges = new Set(graphData.edges.map((edge) => edge.type)); document.querySelectorAll('#edge-filters input').forEach((input) => input.checked = true); applyFilters(); }); await loadProject(select.value); } catch (error) { console.error(error); setEmpty(true, 'Unable to load the local graph. Is RoGraph running?'); } }
init();
