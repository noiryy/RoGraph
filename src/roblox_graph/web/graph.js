const palette = { Script: '#ff676f', LocalScript: '#ff8590', ModuleScript: '#fb7185', RemoteEvent: '#ff9d65', RemoteFunction: '#ffc16b', Service: '#f3c85a', DataStore: '#df6bab', OrderedDataStore: '#df6bab', CollectionServiceTag: '#c9a6ff', Attribute: '#e87fae', Folder: '#b99ba1', Model: '#c9a37b', Place: '#ffeff0', RobloxInstance: '#b99ba1' };
const THEME_STORAGE_KEY = 'rograph.theme';
const LARGE_GRAPH_THRESHOLD = 400;
const OVERVIEW_NODE_LIMIT = 200;
const OVERVIEW_EDGE_LIMIT = 400;
const OVERVIEW_RENDER_LIMIT = 90;
let cy; let graphData = { nodes: [], edges: [] }; let activeTypes = new Set(); let activeEdges = new Set();
let showingOverview = false;
let renderedNodeCount = 0;
const el = (id) => document.getElementById(id);

async function api(path) { const response = await fetch(path); if (!response.ok) throw new Error(await response.text()); return response.json(); }
function escape(value) { return String(value ?? '').replace(/[&<>"']/g, (letter) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' }[letter])); }
function setEmpty(visible, message) { const state = el('empty-state'); state.classList.toggle('is-hidden', !visible); if (message) state.querySelector('p').textContent = message; }
function graphTheme() { const style = getComputedStyle(document.documentElement); return { accent: style.getPropertyValue('--accent').trim(), edge: style.getPropertyValue('--graph-edge').trim(), label: style.getPropertyValue('--node-label').trim(), surface: style.getPropertyValue('--surface').trim(), background: style.getPropertyValue('--bg').trim() }; }
function updateThemeControl() { const dark = document.documentElement.dataset.theme === 'dark'; const button = el('theme-toggle'); el('theme-icon').textContent = dark ? '☼' : '☾'; button.title = dark ? 'Switch to light mode' : 'Switch to dark mode'; button.setAttribute('aria-label', button.title); }
function applyTheme(theme, persist = true) { document.documentElement.dataset.theme = theme; if (persist) localStorage.setItem(THEME_STORAGE_KEY, theme); updateThemeControl(); if (cy) { makeGraph(); applyFilters(); } }
function toggleTheme() { applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'); }

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
  const theme = graphTheme();
  const compact = showingOverview;
  const degrees = new Map();
  graphData.edges.forEach((edge) => {
    degrees.set(edge.source_id, (degrees.get(edge.source_id) || 0) + 1);
    degrees.set(edge.target_id, (degrees.get(edge.target_id) || 0) + 1);
  });
  const visibleNodes = compact
    ? graphData.nodes
      .filter((node) => degrees.has(node.id))
      .sort((left, right) => (degrees.get(right.id) || 0) - (degrees.get(left.id) || 0) || left.id.localeCompare(right.id))
      .slice(0, OVERVIEW_RENDER_LIMIT)
    : graphData.nodes;
  const visibleNodeIds = new Set(visibleNodes.map((node) => node.id));
  const visibleEdges = compact
    ? graphData.edges.filter((edge) => visibleNodeIds.has(edge.source_id) && visibleNodeIds.has(edge.target_id))
    : graphData.edges;
  renderedNodeCount = visibleNodes.length;
  const elements = [
    ...visibleNodes.map((node) => {
      const degree = degrees.get(node.id) || 0;
      const label = compact ? '' : node.name;
      return { data: { ...node, degree, label, color: palette[node.type] || '#91a0b9' }, classes: compact ? 'overview-node' : '' };
    }),
    ...visibleEdges.map((edge) => ({ data: { ...edge, source: edge.source_id, target: edge.target_id }, classes: compact ? 'overview-edge' : '' })),
  ];
  if (cy) cy.destroy();
  cy = cytoscape({ container: el('cy'), elements, wheelSensitivity: .18, style: [
    { selector: 'node', style: { 'background-color':'data(color)', label:'data(label)', color:theme.label, 'font-size':9, 'font-weight':600, 'text-valign':'bottom', 'text-margin-y':7, 'text-outline-width':2, 'text-outline-color':theme.background, width: 'mapData(degree, 0, 20, 15, 34)', height: 'mapData(degree, 0, 20, 15, 34)', 'border-width':0, 'overlay-opacity':0 } },
    { selector: 'node[type = "ModuleScript"]', style: { shape:'round-rectangle' } }, { selector: 'node[type = "RemoteEvent"], node[type = "RemoteFunction"]', style: { shape:'diamond' } }, { selector: 'node[type = "Service"]', style: { shape:'hexagon' } },
    { selector: 'edge', style: { width:1, 'line-color':theme.edge, 'target-arrow-color':theme.edge, 'target-arrow-shape':'triangle', 'curve-style':'bezier', opacity:.5 } },
    { selector: 'edge.overview-edge', style: { width:.75, 'target-arrow-shape':'none', 'curve-style':'unbundled-bezier', opacity:.26 } },
    { selector: 'node.overview-node', style: { 'underlay-color':'data(color)', 'underlay-opacity':.16, 'underlay-padding':7 } },
    { selector: '.focused', style: { 'border-width':0, 'underlay-color':theme.label, 'underlay-opacity':.28, 'underlay-padding':10, 'z-index':9 } }, { selector: '.neighbour', style: { 'border-width':0, 'underlay-color':theme.accent, 'underlay-opacity':.2, 'underlay-padding':6, opacity:1 } }, { selector: '.faded', style: { opacity:.11 } }, { selector: '.selected-edge', style: { width:2.5, 'line-color':theme.accent, 'target-arrow-color':theme.accent, opacity:1 } },
  ], layout: compact
    ? { name:'circle', animate:false, radius:320, padding:80, spacingFactor:1.08, startAngle:Math.PI / 2 }
    : { name:'cose', animate:false, idealEdgeLength:100, nodeRepulsion:6000, gravity:.14, padding:46 } });
  cy.on('tap', 'node', (event) => focusNode(event.target)); cy.on('mouseover', 'node', (event) => highlight(event.target)); cy.on('mouseout', 'node', () => clearHighlight()); cy.on('tap', (event) => { if (event.target === cy) { clearHighlight(); el('detail-panel').classList.add('is-hidden'); } });
}
function highlight(node) { cy.elements().addClass('faded'); node.removeClass('faded').addClass('focused'); node.neighborhood().removeClass('faded').addClass('neighbour'); node.connectedEdges().addClass('selected-edge'); if (node.hasClass('overview-node')) node.data('label', node.data('name')); }
function clearHighlight() { cy.elements().removeClass('faded focused neighbour selected-edge'); cy.nodes('.overview-node').forEach((node) => node.data('label', '')); }
async function focusNode(node) {
  highlight(node); cy.animate({ center:{ eles:node }, zoom:Math.max(cy.zoom(), 1.2) }, { duration:250 }); const data = node.data(); const incoming = node.incomers('edge'); const outgoing = node.outgoers('edge');
  el('detail-type').textContent = data.type; el('detail-name').textContent = data.name; el('detail-path').textContent = data.path || 'No path'; el('incoming-count').textContent = incoming.length; el('outgoing-count').textContent = outgoing.length;
  const relationships = [...incoming, ...outgoing].slice(0, 20).map((edge) => { const other = edge.source().id() === node.id() ? edge.target() : edge.source(); return `<li><small>${escape(edge.data('type'))}</small>${escape(other.data('name'))}</li>`; }).join(''); el('relationships').innerHTML = relationships || '<li>No direct relationships</li>';
  const fullNode = data.source ? data : await api(`/api/nodes/${encodeURIComponent(data.id)}`);
  const source = fullNode.source || ''; el('source-section').style.display = source ? 'block' : 'none'; el('source-preview').textContent = source.slice(0, 1400); el('detail-panel').classList.remove('is-hidden');
}
function runLayout() { if (!cy) return; const name = el('layout-select').value; cy.layout({ name, animate:!showingOverview, animationDuration:350, padding:45, spacingFactor:1.1, avoidOverlap:true, directed:true, roots: cy.nodes().filter((node) => node.data('type') === 'Place') }).run(); }
async function search() { const query = el('search-input').value.trim(); const projectId = el('project-select').value; if (!query || !projectId) return; const data = await api(`/api/search?project_id=${encodeURIComponent(projectId)}&query=${encodeURIComponent(query)}`); if (data.results[0] && cy) focusNode(cy.getElementById(data.results[0].id)); }
async function loadProject(projectId) {
  if (!projectId) { setEmpty(true); return; }
  const overview = await api(`/api/projects/${encodeURIComponent(projectId)}/overview`);
  showingOverview = overview.nodes > LARGE_GRAPH_THRESHOLD;
  el('layout-select').value = showingOverview ? 'circle' : 'cose';
  const params = new URLSearchParams({ project_id: projectId });
  if (showingOverview) { params.set('limit', OVERVIEW_NODE_LIMIT); params.set('edge_limit', OVERVIEW_EDGE_LIMIT); params.set('order', 'connected'); }
  const data = await api(`/api/graph?${params}`);
  graphData = data;
  setEmpty(!data.nodes.length, data.nodes.length ? '' : 'This project has no architectural nodes yet.');
  populateFilters(); makeGraph();
  el('graph-stats').textContent = showingOverview
    ? `Showing ${renderedNodeCount.toLocaleString()} key nodes of ${overview.nodes.toLocaleString()} · optimized overview · ${overview.community_count} areas`
    : `${data.nodes.length.toLocaleString()} nodes · ${data.edges.length.toLocaleString()} edges · ${overview.community_count} areas`;
}
function connectUpdates() { const protocol = location.protocol === 'https:' ? 'wss' : 'ws'; const socket = new WebSocket(`${protocol}://${location.host}/ws/graph`); socket.onmessage = async (message) => { const event = JSON.parse(message.data); if (event.project_id === el('project-select').value) await loadProject(event.project_id); }; socket.onclose = () => window.setTimeout(connectUpdates, 1_000); }
async function init() {
  try {
    applyTheme(document.documentElement.dataset.theme || 'dark', false);
    const { projects } = await api('/api/projects');
    const select = el('project-select');
    projects.forEach((project) => {
      const option = document.createElement('option');
      option.value = project.id;
      option.textContent = project.name;
      select.append(option);
    });
    select.addEventListener('change', () => loadProject(select.value));
    el('search-input').addEventListener('keydown', (event) => { if (event.key === 'Enter') search(); });
    el('theme-toggle').addEventListener('click', toggleTheme);
    el('fit-button').addEventListener('click', () => cy?.fit(undefined, 42));
    el('close-panel').addEventListener('click', () => { el('detail-panel').classList.add('is-hidden'); clearHighlight(); });
    el('layout-select').addEventListener('change', runLayout);
    el('all-types').addEventListener('click', () => {
      activeTypes = new Set(graphData.nodes.map((node) => node.type));
      document.querySelectorAll('#node-filters input').forEach((input) => input.checked = true);
      applyFilters();
    });
    el('all-edges').addEventListener('click', () => {
      activeEdges = new Set(graphData.edges.map((edge) => edge.type));
      document.querySelectorAll('#edge-filters input').forEach((input) => input.checked = true);
      applyFilters();
    });
    await loadProject(select.value);
    connectUpdates();
  } catch (error) {
    console.error(error);
    setEmpty(true, 'Unable to load the local graph. Is RoGraph running?');
  }
}
init();
