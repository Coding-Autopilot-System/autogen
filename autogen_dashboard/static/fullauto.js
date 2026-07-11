const state = {
  nodes: new Map(),
  edges: new Map(),
  activeNode: null,
};

// Node Layout Positions (simple grid/flow mapping based on node type/id for aesthetics)
const layoutMap = {
  'meta-manager': { top: '50px', left: '50px' },
  'planner': { top: '200px', left: '300px' },
  'implementer': { top: '50px', left: '300px' },
  'sandbox': { top: '125px', left: '600px' },
};

function initSwarmTelemetry() {
  const evtSource = new EventSource('/api/swarm/events');
  
  evtSource.addEventListener('snapshot', (e) => {
    const data = JSON.parse(e.data);
    
    // Clear existing
    document.getElementById('graph-nodes-container').innerHTML = '';
    document.getElementById('svg-layer').innerHTML = '';
    state.nodes.clear();
    state.edges.clear();
    
    if (data.nodes) data.nodes.forEach(n => createNode(n));
    if (data.edges) data.edges.forEach(edge => createEdge(edge));
  });

  evtSource.addEventListener('node_created', (e) => {
    createNode(JSON.parse(e.data));
  });

  evtSource.addEventListener('node_update', (e) => {
    updateNode(JSON.parse(e.data));
  });

  evtSource.addEventListener('edge_created', (e) => {
    createEdge(JSON.parse(e.data));
  });
}

function createNode(nodeData) {
  state.nodes.set(nodeData.id, nodeData);
  
  const container = document.getElementById('graph-nodes-container');
  const nodeEl = document.createElement('div');
  nodeEl.className = 'agent-node';
  nodeEl.id = `node-${nodeData.id}`;
  
  const pos = layoutMap[nodeData.id] || { 
    top: `${Math.random() * 200 + 50}px`, 
    left: `${Math.random() * 400 + 50}px` 
  };
  nodeEl.style.top = pos.top;
  nodeEl.style.left = pos.left;
  
  nodeEl.innerHTML = `
    <div class="node-header">
      <h3 class="node-title">${nodeData.label || nodeData.id}</h3>
      <span class="node-type">${nodeData.type || 'agent'}</span>
    </div>
    <div class="node-status status-pulsing" id="status-${nodeData.id}">${nodeData.status || 'Idle'}</div>
  `;
  
  nodeEl.onclick = () => selectNode(nodeData.id);
  container.appendChild(nodeEl);
  
  // Auto-select first node
  if (!state.activeNode) selectNode(nodeData.id);
}

function updateNode(nodeData) {
  const existing = state.nodes.get(nodeData.id) || {};
  const merged = { ...existing, ...nodeData };
  state.nodes.set(nodeData.id, merged);
  
  const statusEl = document.getElementById(`status-${nodeData.id}`);
  if (statusEl) {
    statusEl.textContent = merged.status || 'Idle';
    
    // Flash node border to indicate activity
    const nodeEl = document.getElementById(`node-${nodeData.id}`);
    nodeEl.style.borderColor = 'var(--primary)';
    setTimeout(() => {
      if(state.activeNode !== nodeData.id) {
         nodeEl.style.borderColor = 'var(--border-light)';
      } else {
         nodeEl.style.borderColor = 'var(--accent)';
      }
    }, 500);
  }
  
  if (state.activeNode === nodeData.id) {
    renderNodeDetails(merged);
  }
}

function createEdge(edgeData) {
  state.edges.set(edgeData.id, edgeData);
  
  const svg = document.getElementById('svg-layer');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('id', `edge-${edgeData.id}`);
  path.setAttribute('class', 'graph-edge');
  
  updateEdgePath(path, edgeData.source, edgeData.target);
  svg.appendChild(path);
  
  // Highlight edge briefly
  path.classList.add('active');
  setTimeout(() => path.classList.remove('active'), 2000);
}

function updateEdgePath(pathEl, sourceId, targetId) {
  const sourceNode = document.getElementById(`node-${sourceId}`);
  const targetNode = document.getElementById(`node-${targetId}`);
  
  if (sourceNode && targetNode) {
    const sRect = sourceNode.getBoundingClientRect();
    const tRect = targetNode.getBoundingClientRect();
    
    const containerRect = document.querySelector('.node-graph-area').getBoundingClientRect();
    const scrollTop = document.querySelector('.node-graph-area').scrollTop;
    const scrollLeft = document.querySelector('.node-graph-area').scrollLeft;
    
    const sX = (sRect.left - containerRect.left + scrollLeft) + sRect.width;
    const sY = (sRect.top - containerRect.top + scrollTop) + (sRect.height / 2);
    
    const tX = (tRect.left - containerRect.left + scrollLeft);
    const tY = (tRect.top - containerRect.top + scrollTop) + (tRect.height / 2);
    
    // Simple bezier curve
    const cpX1 = sX + (tX - sX) / 2;
    const cpX2 = tX - (tX - sX) / 2;
    
    pathEl.setAttribute('d', `M ${sX} ${sY} C ${cpX1} ${sY}, ${cpX2} ${tY}, ${tX} ${tY}`);
  }
}

function selectNode(nodeId) {
  // Clear previous selection
  document.querySelectorAll('.agent-node').forEach(n => {
    n.classList.remove('active-node');
    n.style.borderColor = 'var(--border-light)';
  });
  
  state.activeNode = nodeId;
  const nodeEl = document.getElementById(`node-${nodeId}`);
  if (nodeEl) {
    nodeEl.classList.add('active-node');
    nodeEl.style.borderColor = 'var(--accent)';
  }
  
  const nodeData = state.nodes.get(nodeId);
  if (nodeData) {
    renderNodeDetails(nodeData);
  }
}

function renderNodeDetails(nodeData) {
  const logsHtml = nodeData.logs ? nodeData.logs.replace(/\n/g, '<br>') : 'No logs available.';
  let toolsHtml = '';
  
  if (nodeData.tools && nodeData.tools.length > 0) {
    toolsHtml = nodeData.tools.map(t => `<span class="tool-log">▶ ${t.name}(${t.args})</span>\n  ↳ ${t.result}`).join('\n\n');
  } else {
    toolsHtml = 'No tool invocations yet.';
  }

  document.getElementById('node-details-content').innerHTML = `
    <div class="detail-section">
      <h3>Dynamic Instructions</h3>
      <div class="detail-box" style="color: #cbd5e1;">${nodeData.instructions || 'Awaiting instructions...'}</div>
    </div>
    
    <div class="detail-section">
      <h3>State Memory</h3>
      <div class="detail-box" style="color: #a78bfa;">${nodeData.memory || 'Empty'}</div>
    </div>
    
    <div class="detail-section">
      <h3>Tool Call Trace</h3>
      <div class="detail-box">${toolsHtml}</div>
    </div>
    
    <div class="detail-section">
      <h3>Execution Logs</h3>
      <div class="detail-box" id="node-logs-box">${logsHtml}</div>
    </div>
  `;
  
  const logsBox = document.getElementById('node-logs-box');
  if(logsBox) logsBox.scrollTop = logsBox.scrollHeight;
}

// Existing Dashboard Functions
function switchTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  
  event.target.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

async function fetchProcessStatus() {
  try {
      const res = await fetch('/api/processes/status');
      const data = await res.json();
      
      ['proxy', 'daemon', 'watchdog', 'ollama'].forEach(proc => {
          const badge = document.getElementById(`${proc}-status`);
          const isRunning = data[proc] === 'Running';
          if (badge) {
              badge.textContent = isRunning ? 'Running' : 'Stopped';
              badge.className = isRunning ? 'status-badge status-running' : 'status-badge status-stopped';
          }
      });
  } catch (err) {
      console.error("Failed to fetch process status", err);
  }
}

async function startProcess(name) {
  await fetch(`/api/processes/${name}/start`, { method: 'POST' });
  fetchProcessStatus();
}

async function stopProcess(name) {
  await fetch(`/api/processes/${name}/stop`, { method: 'POST' });
  fetchProcessStatus();
}

async function fetchStatus() {
  try {
      const res = await fetch('/api/fullauto/status');
      const data = await res.json();
      
      document.getElementById('inbox-count').textContent = data.inbox.length > 0 ? data.inbox.join(", ") : "0 (Idle)";
      
      const editor = document.getElementById('roadmap-editor');
      if (document.activeElement !== editor) {
          editor.value = data.roadmap;
      }
      
      try {
          const wdRes = await fetch('/api/processes/watchdog/logs');
          const wdData = await wdRes.json();
          const wdLogEl = document.getElementById('watchdog-logs');
          if (wdLogEl) wdLogEl.textContent = wdData.logs || "No watchdog events recorded yet.";
      } catch (e) {}

  } catch (err) {
      console.error("Failed to fetch status", err);
  }
}

async function saveRoadmap() {
  const content = document.getElementById('roadmap-editor').value;
  const btn = document.getElementById('btn-save-roadmap');
  btn.textContent = "Saving...";
  try {
      await fetch('/api/fullauto/roadmap', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content })
      });
      btn.textContent = "Saved!";
      setTimeout(() => btn.textContent = "Save Roadmap", 2000);
  } catch (err) {
      btn.textContent = "Error";
      console.error(err);
  }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  initSwarmTelemetry();
  fetchStatus();
  fetchProcessStatus();
  
  setInterval(fetchStatus, 3000);
  setInterval(fetchProcessStatus, 5000);
});
