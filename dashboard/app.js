/**
 * NaqsKAR Dashboard — app.js
 * Fetches /api/v1/analytics, renders clusters on Leaflet map,
 * updates stats and department bars. Auto-refreshes every 30s.
 */

const API_BASE = "http://localhost:8000";
const REFRESH_INTERVAL = 30_000;

// Department colors & emoji
const DEPT_CONFIG = {
    water_supply:  { color: "#3b82f6", emoji: "💧", label: "Water" },
    electricity:   { color: "#f59e0b", emoji: "⚡", label: "Electricity" },
    roads:         { color: "#8b5cf6", emoji: "🛣️", label: "Roads" },
    sanitation:    { color: "#6b7280", emoji: "🗑️", label: "Sanitation" },
    police:        { color: "#ef4444", emoji: "🚔", label: "Police" },
    health:        { color: "#ec4899", emoji: "🏥", label: "Health" },
    education:     { color: "#14b8a6", emoji: "📚", label: "Education" },
    revenue:       { color: "#a855f7", emoji: "💰", label: "Revenue" },
    gas:           { color: "#f97316", emoji: "🔥", label: "Gas" },
    telecom:       { color: "#06b6d4", emoji: "📡", label: "Telecom" },
};

// --- Leaflet Map Init ---
const map = L.map("map", {
    zoomControl: true,
    attributionControl: true,
}).setView([30.3753, 69.3451], 5); // Pakistan center

L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org">OSM</a> &copy; <a href="https://carto.com">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19,
}).addTo(map);

let markersLayer = L.layerGroup().addTo(map);

// --- Fetch Analytics ---
async function fetchAnalytics() {
    const dept = document.getElementById("filter-department").value;
    const region = document.getElementById("filter-region").value;
    const days = document.getElementById("filter-days").value;

    const url = `${API_BASE}/api/v1/analytics?department=${dept}&region=${region}&days=${days}`;

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        updateStatus(true);
        updateStats(data);
        updateDeptBars(data.by_department);
        updateMap(data.active_clusters || []);
    } catch (err) {
        console.error("Analytics fetch failed:", err);
        updateStatus(false);
    }
}

// --- Update Status Indicator ---
function updateStatus(online) {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");
    if (online) {
        dot.className = "status-dot online";
        text.textContent = "Live";
    } else {
        dot.className = "status-dot offline";
        text.textContent = "Disconnected";
    }
}

// --- Update Stats Bar ---
function updateStats(data) {
    document.querySelector("#stat-total .stat-number").textContent = data.total_complaints || 0;
    document.querySelector("#stat-critical .stat-number").textContent = data.by_urgency?.critical || 0;
    document.querySelector("#stat-high .stat-number").textContent = data.by_urgency?.high || 0;
    document.querySelector("#stat-clusters .stat-number").textContent = (data.active_clusters || []).length;
    document.querySelector("#stat-urgency .stat-number").textContent = (data.avg_urgency || 0).toFixed(2);
}

// --- Update Department Bars ---
function updateDeptBars(byDept) {
    const container = document.getElementById("dept-bars");
    if (!byDept || Object.keys(byDept).length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.75rem;">No data yet</p>';
        return;
    }

    const maxCount = Math.max(...Object.values(byDept), 1);
    let html = "";

    for (const [dept, count] of Object.entries(byDept).sort((a, b) => b[1] - a[1])) {
        const cfg = DEPT_CONFIG[dept] || { color: "#6b7280", emoji: "📋", label: dept };
        const pct = Math.round((count / maxCount) * 100);
        html += `
            <div class="dept-row">
                <span class="dept-name">${cfg.emoji} ${cfg.label}</span>
                <div class="dept-bar-bg">
                    <div class="dept-bar-fill" style="width: ${pct}%; background: ${cfg.color};"></div>
                </div>
                <span class="dept-count">${count}</span>
            </div>
        `;
    }
    container.innerHTML = html;
}

// --- Update Map Markers ---
function updateMap(clusters) {
    markersLayer.clearLayers();

    if (!clusters || clusters.length === 0) return;

    const bounds = [];

    clusters.forEach(cluster => {
        if (!cluster.latitude || !cluster.longitude) return;

        const cfg = DEPT_CONFIG[cluster.department] || { color: "#6b7280", emoji: "📋", label: cluster.department };
        const urgencyClass = getUrgencyClass(cluster.avg_urgency);
        const urgencyLabel = getUrgencyLabel(cluster.avg_urgency);

        // Scale marker size by complaint count (min 12, max 40)
        const radius = Math.min(40, Math.max(12, 10 + cluster.complaint_count * 5));

        const marker = L.circleMarker([cluster.latitude, cluster.longitude], {
            radius: radius,
            fillColor: cfg.color,
            color: "#fff",
            weight: 2,
            opacity: 0.9,
            fillOpacity: 0.65,
        });

        marker.bindPopup(`
            <div class="popup-content">
                <h4>${cfg.emoji} ${cfg.label}</h4>
                <p>🔢 <strong>${cluster.complaint_count}</strong> complaint(s)</p>
                <p>⚖️ Weight: <strong>${cluster.weight}</strong></p>
                <p>🚨 Urgency: <span class="urgency-badge ${urgencyClass}">${urgencyLabel} (${cluster.avg_urgency.toFixed(2)})</span></p>
                <p style="font-size: 0.7rem; margin-top: 6px; color: #64748b;">${cluster.cluster_id}</p>
            </div>
        `);

        markersLayer.addLayer(marker);
        bounds.push([cluster.latitude, cluster.longitude]);
    });

    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }
}

function getUrgencyClass(score) {
    if (score > 0.8) return "urgency-critical";
    if (score > 0.6) return "urgency-high";
    if (score > 0.3) return "urgency-medium";
    return "urgency-low";
}

function getUrgencyLabel(score) {
    if (score > 0.8) return "CRITICAL";
    if (score > 0.6) return "HIGH";
    if (score > 0.3) return "MEDIUM";
    return "LOW";
}

// --- Submit Test Complaint ---
async function submitTestComplaint() {
    const text = document.getElementById("test-text").value.trim();
    if (!text) return;

    const resultDiv = document.getElementById("test-result");
    const btn = document.getElementById("btn-submit");
    btn.textContent = "Classifying...";
    btn.disabled = true;
    resultDiv.textContent = "";

    try {
        const res = await fetch(`${API_BASE}/api/v1/classify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });

        const data = await res.json();
        const cls = data.classification;
        const loc = data.location;
        const cfg = DEPT_CONFIG[cls?.department] || { emoji: "📋", label: cls?.department };
        const urgClass = getUrgencyClass(cls?.urgency_score || 0);

        resultDiv.innerHTML = `
            <div style="margin-top: 6px;">
                <span class="result-tag" style="background: rgba(0,200,83,0.15); color: #00c853;">✅ ${cls?.department}</span>
                <span class="result-tag ${urgClass}">${(cls?.urgency_score || 0).toFixed(2)}</span>
                ${loc ? `<span class="result-tag" style="background: rgba(59,130,246,0.15); color: #3b82f6;">📍 ${loc.resolved_name}</span>` : ""}
            </div>
            <p style="margin-top: 6px; direction: rtl; font-family: inherit;">${data.suggested_response_urdu || ""}</p>
        `;

        // Refresh map after new complaint
        setTimeout(fetchAnalytics, 500);
    } catch (err) {
        resultDiv.textContent = `Error: ${err.message}`;
    } finally {
        btn.textContent = "Submit & Classify";
        btn.disabled = false;
    }
}

// --- Event Listeners ---
document.getElementById("filter-department").addEventListener("change", fetchAnalytics);
document.getElementById("filter-region").addEventListener("change", fetchAnalytics);
document.getElementById("filter-days").addEventListener("input", function() {
    document.getElementById("days-label").textContent = `${this.value} days`;
    fetchAnalytics();
});

// --- Init ---
fetchAnalytics();
setInterval(fetchAnalytics, REFRESH_INTERVAL);
