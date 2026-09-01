/* ==========================================================================
   SafeZone - Hazard Assessment and Relocation Planning System
   SIH 2026 Problem Statement ID: SIH26191 | NDRF / Ministry of Home Affairs
   Modular Vanilla JavaScript (No Frameworks)
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    initGlobalControls();
});

// ==========================================
// 1. GLOBAL CONTROLS & UTILITIES
// ==========================================

function initGlobalControls() {
    // Clock Ticker
    const clockEl = document.getElementById("systemClock");
    if (clockEl) {
        setInterval(() => {
            const now = new Date();
            clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: false });
        }, 1000);
    }

    // Mobile Sidebar Drawer Toggle
    const toggleBtn = document.getElementById("mobileToggleBtn");
    const closeBtn = document.getElementById("mobileCloseBtn");
    const sidebar = document.getElementById("appSidebar");

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => sidebar.classList.add("mobile-open"));
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener("click", () => sidebar.classList.remove("mobile-open"));
    }

    // Login Page Handler
    initLoginControls();
    initLandingCanvas();
}

function getRiskCategoryBadge(category) {
    const cat = (category || "").toUpperCase();
    if (cat === "CRITICAL") return `<span class="risk-badge critical">CRITICAL</span>`;
    if (cat === "HIGH")     return `<span class="risk-badge high">HIGH</span>`;
    if (cat === "MODERATE") return `<span class="risk-badge moderate">MODERATE</span>`;
    return `<span class="risk-badge low">LOW</span>`;
}

function getRiskColorHex(score) {
    if (score >= 70) return "#dc2626"; // Critical Red
    if (score >= 50) return "#ea580c"; // High Orange
    if (score >= 30) return "#d97706"; // Moderate Amber
    return "#16a34a";                  // Low Green
}

// ==========================================
// 2. LOGIN PAGE CONTROLS & ANIMATION
// ==========================================

function initLoginControls() {
    const showPass = document.getElementById("showPasswordToggle");
    const passInput = document.getElementById("password");
    const fillDemoBtn = document.getElementById("fillDemoBtn");
    const userInput = document.getElementById("username");

    if (showPass && passInput) {
        showPass.addEventListener("change", function() {
            passInput.type = this.checked ? "text" : "password";
        });
    }

    if (fillDemoBtn && userInput && passInput) {
        fillDemoBtn.addEventListener("click", function() {
            userInput.value = "admin";
            passInput.value = "admin123";
        });
    }

    const loginCanvas = document.getElementById("loginCanvas");
    if (loginCanvas) {
        const ctx = loginCanvas.getContext("2d");
        let width = (loginCanvas.width = loginCanvas.offsetWidth);
        let height = (loginCanvas.height = loginCanvas.offsetHeight);

        const markers = Array.from({ length: 15 }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,
            radius: Math.random() * 4 + 2,
            speed: Math.random() * 0.5 + 0.2,
            color: ["#ef4444", "#f59e0b", "#10b981", "#3b82f6"][Math.floor(Math.random() * 4)]
        }));

        function draw() {
            ctx.clearRect(0, 0, width, height);
            
            // Draw connecting mesh
            for (let i = 0; i < markers.length; i++) {
                for (let j = i + 1; j < markers.length; j++) {
                    const dx = markers[i].x - markers[j].x;
                    const dy = markers[i].y - markers[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 120) {
                        ctx.beginPath();
                        ctx.moveTo(markers[i].x, markers[i].y);
                        ctx.lineTo(markers[j].x, markers[j].y);
                        ctx.strokeStyle = `rgba(148, 163, 184, ${0.25 - dist / 500})`;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }
            }

            // Draw floating markers
            markers.forEach(m => {
                ctx.beginPath();
                ctx.arc(m.x, m.y, m.radius, 0, Math.PI * 2);
                ctx.fillStyle = m.color;
                ctx.fill();

                m.y -= m.speed;
                if (m.y < 0) m.y = height;
            });

            requestAnimationFrame(draw);
        }
        draw();
    }
}

function initLandingCanvas() {
    const canvas = document.getElementById("landingCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let width = (canvas.width = canvas.offsetWidth);
    let height = (canvas.height = canvas.offsetHeight);

    let offset = 0;
    function animateTerrain() {
        ctx.clearRect(0, 0, width, height);
        
        ctx.beginPath();
        ctx.moveTo(0, height);
        for (let x = 0; x <= width; x += 10) {
            const y = Math.sin((x + offset) * 0.01) * 30 + Math.cos((x + offset) * 0.02) * 20 + height * 0.6;
            ctx.lineTo(x, y);
        }
        ctx.lineTo(width, height);
        ctx.fillStyle = "rgba(30, 58, 138, 0.4)";
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(0, height);
        for (let x = 0; x <= width; x += 10) {
            const y = Math.sin((x - offset) * 0.015) * 20 + Math.cos((x + offset) * 0.01) * 15 + height * 0.75;
            ctx.lineTo(x, y);
        }
        ctx.lineTo(width, height);
        ctx.fillStyle = "rgba(14, 165, 233, 0.3)";
        ctx.fill();

        offset += 0.8;
        requestAnimationFrame(animateTerrain);
    }
    animateTerrain();
}

// ==========================================
// 3. DASHBOARD VIEW CONTROLS
// ==========================================

function initDashboardView() {
    fetch("/api/dashboard")
        .then(res => res.json())
        .then(data => {
            // Stat Cards
            document.getElementById("statTotalHabs").textContent = data.stats.total_habitations;
            document.getElementById("statHighRisk").textContent = data.stats.high_risk_habitations;
            document.getElementById("statRedZone").textContent = data.stats.red_zone_habitations;
            document.getElementById("statRelocReq").textContent = data.stats.relocation_required;
            document.getElementById("statSafeCap").textContent = data.stats.available_safe_capacity.toLocaleString();
            document.getElementById("statAvgRisk").textContent = data.stats.average_risk_score;

            // Render Charts
            renderRiskDistChart(data.charts.risk_distribution);
            renderHazardDistChart(data.charts.hazard_distribution);
            renderRelocStatusChart(data.charts.relocation_status);

            // Render Map
            initDashboardMap(data.recent_habitations);

            // Render Recent Habitations Table
            renderRecentHabsTable(data.recent_habitations);

            // Render Active Alerts Stream
            renderDashboardAlerts(data.recent_alerts);
        })
        .catch(err => console.error("Error fetching dashboard data:", err));
}

function initDashboardMap(habitations) {
    const mapContainer = document.getElementById("dashboardMap");
    if (!mapContainer || typeof L === "undefined") return;

    const map = L.map("dashboardMap").setView([20.5937, 78.9629], 5);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Plot Habitations Markers
    habitations.forEach(hab => {
        const color = getRiskColorHex(hab.current_risk_score);
        const circle = L.circleMarker([hab.latitude, hab.longitude], {
            radius: 9,
            fillColor: color,
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        }).addTo(map);

        const popupContent = `
            <div style="font-family: sans-serif; font-size: 13px;">
                <strong style="font-size: 14px; color: #0f172a;">${hab.name}</strong><br>
                <span style="color: #64748b;">${hab.district}, ${hab.state}</span><br>
                <div style="margin-top: 6px;">
                    <strong>Risk Score:</strong> <span style="color: ${color}; font-weight: bold;">${hab.current_risk_score}/100 (${hab.risk_category})</span><br>
                    <strong>Primary Hazard:</strong> ${hab.primary_hazard}<br>
                    <strong>Population:</strong> ${hab.population} (Vulnerable: ${hab.vulnerable_population})<br>
                    <strong>Status:</strong> ${hab.relocation_status}
                </div>
            </div>
        `;
        circle.bindPopup(popupContent);
    });

    // Also fetch and plot Safe Zone markers
    fetch("/api/safe-zones")
        .then(res => res.json())
        .then(safeZones => {
            safeZones.forEach(sz => {
                const szMarker = L.circleMarker([sz.latitude, sz.longitude], {
                    radius: 10,
                    fillColor: "#0284c7",
                    color: "#ffffff",
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.9
                }).addTo(map);

                const szPopup = `
                    <div style="font-family: sans-serif; font-size: 13px;">
                        <span style="background: #e0f2fe; color: #0369a1; padding: 2px 6px; font-weight: bold; border-radius: 3px; font-size: 11px;">SAFE ZONE</span><br>
                        <strong style="font-size: 14px; color: #0f172a;">${sz.name}</strong><br>
                        <span style="color: #64748b;">${sz.location_name}, ${sz.district}</span><br>
                        <div style="margin-top: 6px;">
                            <strong>Total Capacity:</strong> ${sz.estimated_capacity.toLocaleString()}<br>
                            <strong>Current Occupancy:</strong> ${sz.current_occupancy.toLocaleString()}<br>
                            <strong>Remaining Margin:</strong> <span style="color: #16a34a; font-weight: bold;">${sz.remaining_capacity.toLocaleString()}</span><br>
                            <strong>Suitability:</strong> ${sz.suitability_score}%
                        </div>
                    </div>
                `;
                szMarker.bindPopup(szPopup);
            });
        });
}

function renderRiskDistChart(dist) {
    const ctx = document.getElementById("riskDistChart");
    if (!ctx) return;
    new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Low", "Moderate", "High", "Critical"],
            datasets: [{
                data: [dist.LOW || 0, dist.MODERATE || 0, dist.HIGH || 0, dist.CRITICAL || 0],
                backgroundColor: ["#16a34a", "#d97706", "#ea580c", "#dc2626"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "bottom" } }
        }
    });
}

function renderHazardDistChart(dist) {
    const ctx = document.getElementById("hazardDistChart");
    if (!ctx) return;
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: Object.keys(dist),
            datasets: [{
                label: "Settlements Count",
                data: Object.values(dist),
                backgroundColor: "#3b82f6"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

function renderRelocStatusChart(dist) {
    const ctx = document.getElementById("relocStatusChart");
    if (!ctx) return;
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: Object.keys(dist),
            datasets: [{
                label: "Settlements",
                data: Object.values(dist),
                backgroundColor: ["#dc2626", "#ea580c", "#3b82f6", "#16a34a"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

function renderRecentHabsTable(habs) {
    const tbody = document.querySelector("#recentHabsTable tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    habs.forEach(h => {
        const isRedZone = h.current_risk_score >= 70;
        const tr = document.createElement("tr");
        if (isRedZone) tr.classList.add("red-zone-row");
        tr.innerHTML = `
            <td><code>${h.habitation_code}</code></td>
            <td><strong>${h.name}</strong></td>
            <td>${h.district}</td>
            <td>${h.primary_hazard}</td>
            <td><strong>${h.current_risk_score}/100</strong></td>
            <td>${getRiskCategoryBadge(h.risk_category)}</td>
            <td><span class="badge ${h.relocation_status === 'Relocation Required' ? 'badge-danger' : 'badge-outline'}">${h.relocation_status}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderDashboardAlerts(alerts) {
    const container = document.getElementById("dashboardAlertsList");
    if (!container) return;
    container.innerHTML = "";

    if (!alerts || alerts.length === 0) {
        container.innerHTML = `<div class="text-center text-muted py-3">No active critical alerts.</div>`;
        return;
    }

    alerts.forEach(a => {
        const item = document.createElement("div");
        item.className = `alert-stream-item ${a.severity.toLowerCase()}`;
        item.innerHTML = `
            <div class="alert-stream-header">
                <span>${a.habitation_name} - ${a.alert_type}</span>
                <span class="badge ${a.severity === 'Critical' ? 'badge-danger' : 'badge-warning'}">${a.severity}</span>
            </div>
            <div>${a.message}</div>
            <div class="text-muted mt-1" style="font-size: 0.72rem;">${a.timestamp}</div>
        `;
        container.appendChild(item);
    });
}

// ==========================================
// 4. HABITATIONS DIRECTORY CONTROLS
// ==========================================

let globalHabitationsList = [];

function initHabitationsView() {
    loadHabitations();

    const searchInput = document.getElementById("habSearch");
    const riskFilter = document.getElementById("riskFilter");
    const hazardFilter = document.getElementById("hazardFilter");
    const resetBtn = document.getElementById("resetHabFiltersBtn");

    if (searchInput) searchInput.addEventListener("input", filterHabitations);
    if (riskFilter) riskFilter.addEventListener("change", filterHabitations);
    if (hazardFilter) hazardFilter.addEventListener("change", filterHabitations);
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            if (searchInput) searchInput.value = "";
            if (riskFilter) riskFilter.value = "ALL";
            if (hazardFilter) hazardFilter.value = "ALL";
            filterHabitations();
        });
    }

    const modalCloseBtn = document.getElementById("modalCloseBtn");
    if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeHabModal);
}

function loadHabitations() {
    fetch("/api/habitations")
        .then(res => res.json())
        .then(data => {
            globalHabitationsList = data;
            renderHabitationsTable(data);
        });
}

function filterHabitations() {
    const searchVal = (document.getElementById("habSearch")?.value || "").toLowerCase();
    const riskVal = document.getElementById("riskFilter")?.value || "ALL";
    const hazardVal = document.getElementById("hazardFilter")?.value || "ALL";

    const filtered = globalHabitationsList.filter(h => {
        const matchesSearch = h.name.toLowerCase().includes(searchVal) ||
                              h.district.toLowerCase().includes(searchVal) ||
                              h.habitation_code.toLowerCase().includes(searchVal);
        const matchesRisk = riskVal === "ALL" || h.risk_category === riskVal;
        const matchesHazard = hazardVal === "ALL" || h.primary_hazard === hazardVal;
        return matchesSearch && matchesRisk && matchesHazard;
    });

    renderHabitationsTable(filtered);
}

function renderHabitationsTable(list) {
    const tbody = document.getElementById("habitationsTableBody");
    const countBadge = document.getElementById("habCountBadge");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (countBadge) countBadge.textContent = `${list.length} Items`;

    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" class="text-center py-4 text-muted">No habitations match selected criteria.</td></tr>`;
        return;
    }

    list.forEach(h => {
        const isRedZone = h.current_risk_score >= 70;
        const tr = document.createElement("tr");
        if (isRedZone) tr.classList.add("red-zone-row");

        tr.innerHTML = `
            <td><code>${h.habitation_code}</code></td>
            <td><strong>${h.name}</strong></td>
            <td>${h.district}, ${h.state}</td>
            <td>${h.population} <span class="text-muted">(${h.vulnerable_population} vuln)</span></td>
            <td>${h.elevation}m</td>
            <td>${h.road_accessibility}/100</td>
            <td>${h.primary_hazard}</td>
            <td><strong>${h.current_risk_score}/100</strong></td>
            <td>${getRiskCategoryBadge(h.risk_category)}</td>
            <td><span class="badge ${h.relocation_status === 'Relocation Required' ? 'badge-danger' : 'badge-outline'}">${h.relocation_status}</span></td>
            <td>
                <button class="btn btn-outline btn-xs" onclick="openHabModal(${h.id})">Details</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openHabModal(habId) {
    const modal = document.getElementById("habModalOverlay");
    const body = document.getElementById("modalHabContent");
    const title = document.getElementById("modalHabName");
    const relocBtn = document.getElementById("modalRelocBtn");
    if (!modal || !body) return;

    modal.classList.add("active");
    body.innerHTML = `<div class="text-center py-4">Loading habitation record...</div>`;

    fetch(`/api/habitations/${habId}`)
        .then(res => res.json())
        .then(data => {
            const h = data.habitation;
            if (title) title.textContent = `${h.name} (${h.habitation_code})`;
            if (relocBtn) relocBtn.href = `/relocation?hab_id=${h.id}`;

            body.innerHTML = `
                <div class="metrics-row mb-3">
                    <div class="metric-box"><span class="lbl">District / State</span><span class="val">${h.district}, ${h.state}</span></div>
                    <div class="metric-box"><span class="lbl">Total Population</span><span class="val">${h.population}</span></div>
                    <div class="metric-box"><span class="lbl">Vulnerable Pop</span><span class="val text-danger">${h.vulnerable_population}</span></div>
                    <div class="metric-box"><span class="lbl">Risk Score</span><span class="val text-danger">${h.current_risk_score}/100 (${h.risk_category})</span></div>
                </div>

                <div class="row">
                    <div class="col-6">
                        <p><strong>Primary Hazard:</strong> ${h.primary_hazard}</p>
                        <p><strong>Elevation:</strong> ${h.elevation} meters</p>
                        <p><strong>Road Accessibility Index:</strong> ${h.road_accessibility}/100</p>
                    </div>
                    <div class="col-6">
                        <p><strong>Nearest Hospital:</strong> ${h.nearest_hospital_km} km</p>
                        <p><strong>Nearest School:</strong> ${h.nearest_school_km} km</p>
                        <p><strong>Relocation Status:</strong> <span class="badge badge-danger">${h.relocation_status}</span></p>
                    </div>
                </div>
            `;
        });
}

function closeHabModal() {
    const modal = document.getElementById("habModalOverlay");
    if (modal) modal.classList.remove("active");
}

// ==========================================
// 5. HAZARD ASSESSMENT VIEW
// ==========================================

function initHazardsView() {
    populateHabitationSelect("selectHabitation");

    // Slider inputs live update listeners
    const sliders = [
        { id: "hazardExposureSlider", valId: "valHazardExp", suffix: "" },
        { id: "rainfallSlider", valId: "valRainfall", suffix: "" },
        { id: "slopeSlider", valId: "valSlope", suffix: "°" },
        { id: "historicalFreqSlider", valId: "valHistFreq", suffix: "" },
        { id: "vulnerablePopSlider", valId: "valVulnPop", suffix: "%" }
    ];

    sliders.forEach(s => {
        const input = document.getElementById(s.id);
        const valSpan = document.getElementById(s.valId);
        if (input && valSpan) {
            input.addEventListener("input", () => {
                valSpan.textContent = input.value + s.suffix;
                calculateFormRiskScore();
            });
        }
    });

    const calcBtn = document.getElementById("calcRiskBtn");
    if (calcBtn) calcBtn.addEventListener("click", calculateFormRiskScore);
}

function populateHabitationSelect(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    fetch("/api/habitations")
        .then(res => res.json())
        .then(habs => {
            select.innerHTML = `<option value="">-- Select Habitation --</option>`;
            habs.forEach(h => {
                const opt = document.createElement("option");
                opt.value = h.id;
                opt.textContent = `${h.name} (${h.district}) - Risk: ${h.current_risk_score}`;
                select.appendChild(opt);
            });
        });
}

function calculateFormRiskScore() {
    const hazardExp = parseFloat(document.getElementById("hazardExposureSlider")?.value || 75);
    const rainfall = parseFloat(document.getElementById("rainfallSlider")?.value || 80);
    const slope = parseFloat(document.getElementById("slopeSlider")?.value || 35);
    const histFreq = parseFloat(document.getElementById("historicalFreqSlider")?.value || 70);
    const vulnPop = parseFloat(document.getElementById("vulnerablePopSlider")?.value || 40);
    const roadAccess = parseFloat(document.getElementById("roadAccessInput")?.value || 30);
    const emergencyDist = parseFloat(document.getElementById("emergencyDistInput")?.value || 15);

    const accessRisk = 100 - roadAccess;
    const score = roundVal(
        0.25 * hazardExp +
        0.15 * rainfall +
        0.12 * slope +
        0.15 * vulnPop +
        0.12 * histFreq +
        0.10 * accessRisk +
        0.06 * emergencyDist +
        0.05 * 50
    , 1);

    let category = "LOW";
    let priority = "LOW";
    let badgeClass = "badge-success";

    if (score >= 70) {
        category = "CRITICAL RISK";
        priority = "EMERGENCY";
        badgeClass = "badge-danger";
    } else if (score >= 50) {
        category = "HIGH RISK";
        priority = "HIGH";
        badgeClass = "badge-warning";
    } else if (score >= 30) {
        category = "MODERATE RISK";
        priority = "MEDIUM";
        badgeClass = "badge-info";
    }

    const outScore = document.getElementById("outputRiskScore");
    const outCat = document.getElementById("outputRiskCategory");
    const outPriority = document.getElementById("outputPriority");

    if (outScore) outScore.textContent = score;
    if (outCat) {
        outCat.textContent = category;
        outCat.className = `badge badge-lg ${badgeClass}`;
    }
    if (outPriority) outPriority.textContent = priority;

    // Update Progress Bars
    updateBar("barExp", "factExpScore", roundVal(0.25 * hazardExp + 0.15 * rainfall, 1), 40);
    updateBar("barSlope", "factSlopeScore", roundVal(0.12 * slope, 1), 15);
    updateBar("barVuln", "factVulnScore", roundVal(0.15 * vulnPop, 1), 15);
    updateBar("barHist", "factHistScore", roundVal(0.12 * histFreq, 1), 15);
    updateBar("barAccess", "factAccessScore", roundVal(0.10 * accessRisk + 0.06 * emergencyDist, 1), 15);
}

function updateBar(barId, scoreId, val, maxVal) {
    const bar = document.getElementById(barId);
    const scoreSpan = document.getElementById(scoreId);
    if (scoreSpan) scoreSpan.textContent = val;
    if (bar) {
        const pct = Math.min(100, Math.max(0, (val / maxVal) * 100));
        bar.style.width = `${pct}%`;
    }
}

function roundVal(num, decimals) {
    return Number(Math.round(num + 'e' + decimals) + 'e-' + decimals);
}

// ==========================================
// 6. AI RISK ANALYSIS VIEW (ML PREDICT)
// ==========================================

function initRiskAnalysisView() {
    populateHabitationSelect("mlHabSelect");

    const form = document.getElementById("mlPredictForm");
    if (form) {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            runMlPredict();
        });
    }

    const habSelect = document.getElementById("mlHabSelect");
    if (habSelect) {
        habSelect.addEventListener("change", function() {
            if (!this.value) return;
            fetch(`/api/habitations/${this.value}`)
                .then(res => res.json())
                .then(data => {
                    const h = data.habitation;
                    document.getElementById("mlHazardExp").value = 75;
                    document.getElementById("mlRainfall").value = 80;
                    document.getElementById("mlSlope").value = 35;
                    document.getElementById("mlPopDensity").value = 50;
                    document.getElementById("mlVulnPop").value = Math.round((h.vulnerable_population / h.population) * 100);
                    document.getElementById("mlHistFreq").value = 70;
                    document.getElementById("mlRoadAccess").value = h.road_accessibility;
                    document.getElementById("mlEmergencyDist").value = h.nearest_hospital_km;
                    document.getElementById("mlInfraCond").value = 40;
                    document.getElementById("mlElevation").value = h.elevation;
                });
        });
    }
}

function runMlPredict() {
    const payload = {
        habitation_id: document.getElementById("mlHabSelect")?.value || null,
        hazard_exposure: parseFloat(document.getElementById("mlHazardExp")?.value || 75),
        rainfall_exposure: parseFloat(document.getElementById("mlRainfall")?.value || 82),
        slope: parseFloat(document.getElementById("mlSlope")?.value || 40),
        population_density: parseFloat(document.getElementById("mlPopDensity")?.value || 55),
        vulnerable_population: parseFloat(document.getElementById("mlVulnPop")?.value || 42),
        historical_frequency: parseFloat(document.getElementById("mlHistFreq")?.value || 70),
        road_accessibility: parseFloat(document.getElementById("mlRoadAccess")?.value || 25),
        emergency_distance: parseFloat(document.getElementById("mlEmergencyDist")?.value || 16.5),
        infrastructure_condition: parseFloat(document.getElementById("mlInfraCond")?.value || 35),
        elevation: parseFloat(document.getElementById("mlElevation")?.value || 1450)
    };

    fetch("/api/risk/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("mlResCategory").textContent = data.risk_category;
        document.getElementById("mlResScore").textContent = `${data.risk_score} / 100`;
        document.getElementById("mlResConf").textContent = `${Math.round(data.confidence * 100)}%`;
        document.getElementById("mlResPriority").textContent = data.priority;
    });
}

// ==========================================
// 7. SAFE ZONES VIEW
// ==========================================

function initSafeZonesView() {
    fetch("/api/safe-zones")
        .then(res => res.json())
        .then(data => {
            renderSafeZonesGrid(data);
        });
}

function renderSafeZonesGrid(zones) {
    const container = document.getElementById("safeZonesGridContainer");
    if (!container) return;
    container.innerHTML = "";

    zones.forEach(sz => {
        const card = document.createElement("div");
        card.className = "sz-card";

        const occPct = sz.occupancy_rate;
        let progressColor = "green";
        if (occPct > 85) progressColor = "red";
        else if (occPct > 65) progressColor = "orange";

        card.innerHTML = `
            <div class="sz-header">
                <div>
                    <div class="sz-title">${sz.name}</div>
                    <div class="sz-location">${sz.location_name}, ${sz.district}</div>
                </div>
                <span class="badge badge-success">${sz.suitability_score}% Suitability</span>
            </div>

            <div class="factor-progress-item my-2">
                <div class="factor-label">
                    <span>Capacity Utilization (${occPct}%)</span>
                    <span>${sz.current_occupancy} / ${sz.estimated_capacity}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill ${progressColor}" style="width: ${occPct}%;"></div>
                </div>
            </div>

            <div class="sz-metrics-grid">
                <div>Available Margin: <strong class="text-green">${sz.remaining_capacity.toLocaleString()} seats</strong></div>
                <div>Area: <strong>${sz.area_sqm.toLocaleString()} m²</strong></div>
                <div>Road Access: <strong>${sz.road_accessibility}/100</strong></div>
                <div>Hospital: <strong>${sz.nearest_hospital_km} km</strong></div>
            </div>

            <div class="d-flex justify-content-between align-items-center mt-2" style="font-size: 0.78rem;">
                <span>Water: <strong>${sz.water_availability ? 'Yes' : 'No'}</strong> | Power: <strong>${sz.power_availability ? 'Yes' : 'No'}</strong></span>
                <code>${sz.site_code}</code>
            </div>
        `;
        container.appendChild(card);
    });
}

// ==========================================
// 8. RELOCATION PLANNING VIEW
// ==========================================

function initRelocationView() {
    populateHabitationSelect("relocHabSelect");

    const matchBtn = document.getElementById("runRelocMatchBtn");
    if (matchBtn) {
        matchBtn.addEventListener("click", runRelocationMatch);
    }
}

function runRelocationMatch() {
    const habId = document.getElementById("relocHabSelect")?.value;
    if (!habId) {
        alert("Please select a target vulnerable habitation first.");
        return;
    }

    fetch(`/api/relocation/${habId}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById("relocResultsContainer").style.display = "block";

            const h = data.habitation;
            document.getElementById("relocHabName").textContent = `${h.name} (${h.habitation_code})`;
            document.getElementById("relocPopVal").textContent = h.population;
            document.getElementById("relocVulnPopVal").textContent = h.vulnerable_population;
            document.getElementById("relocRiskVal").textContent = `${h.current_risk_score} / 100 (${h.risk_category})`;
            document.getElementById("relocHazardVal").textContent = h.primary_hazard;
            document.getElementById("relocLocVal").textContent = `${h.district}, ${h.state}`;
            document.getElementById("relocActionText").textContent = data.recommended_action;

            renderRelocCandidatesTable(data.candidates);
        });
}

function renderRelocCandidatesTable(candidates) {
    const tbody = document.getElementById("relocCandidatesTbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    candidates.forEach((c, idx) => {
        const tr = document.createElement("tr");
        const fits = c.capacity_fits;

        tr.innerHTML = `
            <td><strong>#${idx + 1}</strong></td>
            <td><strong>${c.name}</strong> <code>(${c.site_code})</code></td>
            <td>${c.location_name}, ${c.district}</td>
            <td>${c.distance_km} km</td>
            <td><strong>${c.suitability_score}%</strong></td>
            <td><strong class="${fits ? 'text-green' : 'text-danger'}">${c.remaining_capacity.toLocaleString()} seats</strong></td>
            <td>
                <span class="badge ${fits ? 'badge-success' : 'badge-danger'}">
                    ${fits ? 'Sufficient Capacity' : 'Insufficient Seats'}
                </span>
            </td>
            <td>Road: ${c.road_access}/100</td>
            <td>
                <span class="badge ${idx === 0 && fits ? 'badge-primary' : 'badge-outline'}">
                    ${idx === 0 && fits ? 'Top Recommendation' : 'Candidate'}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// ==========================================
// 9. ALERTS MONITOR VIEW
// ==========================================

function initAlertsView() {
    loadAlerts();

    const sevFilter = document.getElementById("alertSeverityFilter");
    const statFilter = document.getElementById("alertStatusFilter");
    const resetBtn = document.getElementById("resetAlertFiltersBtn");

    if (sevFilter) sevFilter.addEventListener("change", loadAlerts);
    if (statFilter) statFilter.addEventListener("change", loadAlerts);
    if (resetBtn) resetBtn.addEventListener("click", loadAlerts);
}

function loadAlerts() {
    fetch("/api/alerts")
        .then(res => res.json())
        .then(alerts => {
            const sevVal = document.getElementById("alertSeverityFilter")?.value || "ALL";
            const statVal = document.getElementById("alertStatusFilter")?.value || "ALL";

            const filtered = alerts.filter(a => {
                const matchSev = sevVal === "ALL" || a.severity === sevVal;
                const matchStat = statVal === "ALL" || a.status === statVal;
                return matchSev && matchStat;
            });

            renderAlertsTable(filtered);
        });
}

function renderAlertsTable(alerts) {
    const tbody = document.getElementById("alertsTableBody");
    const countBadge = document.getElementById("alertTotalBadge");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (countBadge) countBadge.textContent = `${alerts.length} Alerts`;

    if (alerts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No alerts match selected filters.</td></tr>`;
        return;
    }

    alerts.forEach(a => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><code>ALT-${a.id}</code></td>
            <td><strong>${a.habitation_name}</strong></td>
            <td>${a.district}</td>
            <td>${a.alert_type}</td>
            <td><span class="badge ${a.severity === 'Critical' ? 'badge-danger' : 'badge-warning'}">${a.severity}</span></td>
            <td><strong>${a.risk_score}</strong></td>
            <td style="font-size: 0.75rem;">${a.timestamp}</td>
            <td style="max-width: 250px;">${a.message}</td>
            <td><span class="badge badge-outline">${a.status}</span></td>
            <td>
                ${a.status !== 'Resolved' ? `<button class="btn btn-outline btn-xs" onclick="updateAlertStatus(${a.id}, '${a.status === 'New' ? 'Acknowledged' : 'Resolved'}')">${a.status === 'New' ? 'Acknowledge' : 'Resolve'}</button>` : '<span class="text-muted">-</span>'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateAlertStatus(alertId, newStatus) {
    fetch(`/api/alerts/${alertId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
    })
    .then(res => res.json())
    .then(() => loadAlerts());
}

// ==========================================
// 10. REPORTS VIEW
// ==========================================

function initReportsView() {
    fetch("/api/reports")
        .then(res => res.json())
        .then(data => {
            const s = data.summary;
            document.getElementById("reportGenDate").textContent = s.generated_date;
            document.getElementById("repTotalHabs").textContent = s.total_habitations;
            document.getElementById("repCriticalHabs").textContent = s.critical_habitations;
            document.getElementById("repHighHabs").textContent = s.high_risk_habitations;
            document.getElementById("repRelocReq").textContent = s.relocation_required_count;
            document.getElementById("repTotalCap").textContent = s.total_safe_capacity.toLocaleString();
            document.getElementById("repAvailCap").textContent = s.remaining_safe_capacity.toLocaleString();

            // Red Zone Table
            const redTbody = document.getElementById("reportRedZoneTbody");
            if (redTbody) {
                redTbody.innerHTML = "";
                data.red_zone_habitations.forEach(h => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><code>${h.habitation_code}</code></td>
                        <td><strong>${h.name}</strong></td>
                        <td>${h.district}, ${h.state}</td>
                        <td>${h.primary_hazard}</td>
                        <td>${h.population}</td>
                        <td>${h.vulnerable_population}</td>
                        <td><strong>${h.current_risk_score}</strong></td>
                        <td>${h.risk_category}</td>
                        <td>${h.relocation_status}</td>
                    `;
                    redTbody.appendChild(tr);
                });
            }

            // Safe Zone Table
            const szTbody = document.getElementById("reportSafeZoneTbody");
            if (szTbody) {
                szTbody.innerHTML = "";
                data.safe_zones.forEach(sz => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><code>${sz.site_code}</code></td>
                        <td><strong>${sz.name}</strong></td>
                        <td>${sz.location_name}, ${sz.district}</td>
                        <td>${sz.estimated_capacity.toLocaleString()}</td>
                        <td>${sz.current_occupancy.toLocaleString()}</td>
                        <td><strong>${sz.remaining_capacity.toLocaleString()}</strong></td>
                        <td>${sz.occupancy_rate}%</td>
                        <td>${sz.suitability_score}%</td>
                        <td>Water: ${sz.water_availability ? 'Yes' : 'No'} | Power: ${sz.power_availability ? 'Yes' : 'No'}</td>
                    `;
                    szTbody.appendChild(tr);
                });
            }

            // Relocation Table
            const relocTbody = document.getElementById("reportRelocTbody");
            if (relocTbody) {
                relocTbody.innerHTML = "";
                data.relocation_plans.forEach(rp => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${rp.habitation_name}</strong> (${rp.district})</td>
                        <td>${rp.safe_zone_name}</td>
                        <td>${rp.population_to_relocate}</td>
                        <td>${rp.distance_km} km</td>
                        <td>${rp.suitability_score}%</td>
                        <td><strong>${rp.priority}</strong></td>
                        <td>${rp.recommended_action}</td>
                    `;
                    relocTbody.appendChild(tr);
                });
            }
        });
}
