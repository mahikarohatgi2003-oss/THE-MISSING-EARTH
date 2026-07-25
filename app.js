// The Missing Earth — dashboard + map viewer
// Reads static GeoJSON produced by the Python pipeline (docs/data/*.geojson)
// and renders both the dashboard panels and the interactive Leaflet map.
// No backend, no build step.

const DATA_DIR = "data";
const DONUT_CIRCUMFERENCE = 2 * Math.PI * 52; // r=52 from the SVG

// ---------- Leaflet map setup ----------
const map = L.map("map", { zoomControl: false, minZoom: 3 }).setView([20.5937, 78.9629], 5);
L.control.zoom({ position: "bottomleft" }).addTo(map);

L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
  attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  maxZoom: 20,
}).addTo(map);

let mappedLayer, missingLayer, heatLayer;
let boundsLayers = [];

async function loadGeoJSON(name) {
  try {
    const res = await fetch(`${DATA_DIR}/${name}`);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}

function styleMapped() { return { color: "#38e07a", weight: 1, fillColor: "#38e07a", fillOpacity: 0.5 }; }
function styleMissing() { return { color: "#ff5252", weight: 1.2, fillColor: "#ff5252", fillOpacity: 0.65 }; }

function centroidOfRing(ring) {
  let x = 0, y = 0;
  ring.forEach(([lng, lat]) => { x += lng; y += lat; });
  return [x / ring.length, y / ring.length];
}

async function init() {
  const [mapped, missing, heat, stats] = await Promise.all([
    loadGeoJSON("mapped.geojson"),
    loadGeoJSON("missing.geojson"),
    loadGeoJSON("heatmap.geojson"),
    loadGeoJSON("stats.json"),
  ]);

  if (!mapped && !missing) {
    document.getElementById("empty-state").hidden = false;
    return;
  }

  if (mapped) {
    mappedLayer = L.geoJSON(mapped, {
      style: styleMapped,
      onEachFeature: (f, layer) => layer.bindPopup("Status: already mapped in OSM"),
    }).addTo(map);
    boundsLayers.push(mappedLayer);
  }

  if (missing) {
    missingLayer = L.geoJSON(missing, {
      style: styleMissing,
      onEachFeature: (f, layer) => layer.bindPopup("Status: likely missing from OSM"),
    }).addTo(map);
    boundsLayers.push(missingLayer);
  }

  let heatPoints = [];
  if (heat) {
    heatPoints = heat.features.map((f) => {
      const [lng, lat] = f.geometry.type === "Polygon"
        ? centroidOfRing(f.geometry.coordinates[0])
        : [f.geometry.coordinates[0], f.geometry.coordinates[1]];
      return { lat, lng, intensity: f.properties.intensity ?? 0.5, count: f.properties.missing_count ?? 0 };
    });
    heatLayer = L.heatLayer(
      heatPoints.map((p) => [p.lat, p.lng, p.intensity]),
      { radius: 35, blur: 25, gradient: { 0.2: "#38e07a", 0.5: "#ff9142", 1.0: "#ff5252" } }
    ).addTo(map);
  }

  if (boundsLayers.length) {
    map.fitBounds(L.featureGroup(boundsLayers).getBounds().pad(0.1));
  }

  if (stats) applyDashboardStats(stats);
  drawMiniHeatmap(heatPoints);
  renderPriorityList(heatPoints);
  wireToggles();
}

// ---------- Dashboard panel wiring ----------
function applyDashboardStats(stats) {
  document.getElementById("panel-place-name").textContent = stats.place_name || "Unnamed study area";
  document.getElementById("panel-total-detected").textContent = stats.buildings_total_detected.toLocaleString();
  document.getElementById("panel-missing-count").textContent = stats.buildings_missing.toLocaleString();

  document.getElementById("stat-mapped").textContent = stats.buildings_mapped.toLocaleString();
  document.getElementById("stat-missing").textContent = stats.buildings_missing.toLocaleString();
  document.getElementById("stat-hours").textContent = `≈ ${stats.estimated_volunteer_hours}h`;
  document.getElementById("stat-mappers").textContent = `≈ ${stats.estimated_mappers_for_one_weekend}`;

  document.getElementById("donut-pct").textContent = `${stats.coverage_pct}%`;
  const offset = DONUT_CIRCUMFERENCE * (1 - stats.coverage_pct / 100);
  requestAnimationFrame(() => {
    document.getElementById("donut-fill").style.strokeDashoffset = offset;
  });
}

// ---------- Mini canvas heatmap (independent of Leaflet, for the panel) ----------
function drawMiniHeatmap(points) {
  const canvas = document.getElementById("mini-heatmap");
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  if (!points.length) {
    ctx.fillStyle = "#3a4864";
    ctx.font = "11px 'IBM Plex Mono', monospace";
    ctx.fillText("No priority zones yet", 12, h / 2);
    return;
  }

  const lats = points.map((p) => p.lat), lngs = points.map((p) => p.lng);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const pad = 14;

  function project(lat, lng) {
    const x = pad + ((lng - minLng) / (maxLng - minLng || 1)) * (w - 2 * pad);
    const y = h - pad - ((lat - minLat) / (maxLat - minLat || 1)) * (h - 2 * pad);
    return [x, y];
  }

  ctx.globalCompositeOperation = "lighter";
  points.forEach((p) => {
    const [x, y] = project(p.lat, p.lng);
    const r = 26;
    const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
    const intensity = p.intensity;
    const color = intensity > 0.66 ? "255,82,82" : intensity > 0.33 ? "255,145,66" : "56,224,122";
    grad.addColorStop(0, `rgba(${color},${0.55 * intensity + 0.15})`);
    grad.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalCompositeOperation = "source-over";
}

// ---------- Suggested next edits list ----------
function renderPriorityList(points) {
  const container = document.getElementById("priority-list");
  if (!points.length) return; // leave the "run the pipeline" placeholder

  const top = [...points].sort((a, b) => b.count - a.count).slice(0, 8);
  container.innerHTML = "";
  top.forEach((p) => {
    const div = document.createElement("div");
    div.className = "priority-item";
    div.innerHTML = `
      <div class="priority-item__count">${p.count} buildings</div>
      <div class="priority-item__coords">${p.lat.toFixed(4)}, ${p.lng.toFixed(4)}</div>
    `;
    container.appendChild(div);
  });
}

// ---------- Layer toggles ----------
function wireToggles() {
  document.getElementById("toggle-mapped").addEventListener("change", (e) => {
    if (!mappedLayer) return;
    e.target.checked ? map.addLayer(mappedLayer) : map.removeLayer(mappedLayer);
  });
  document.getElementById("toggle-missing").addEventListener("change", (e) => {
    if (!missingLayer) return;
    e.target.checked ? map.addLayer(missingLayer) : map.removeLayer(missingLayer);
  });
  document.getElementById("toggle-heatmap").addEventListener("change", (e) => {
    if (!heatLayer) return;
    e.target.checked ? map.addLayer(heatLayer) : map.removeLayer(heatLayer);
  });
}

init();
