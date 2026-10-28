// MotoCare AI Telemetry Interface Controller
document.addEventListener("DOMContentLoaded", () => {
    // State variables
    let probChartInstance = null;
    let radarChartInstance = null;
    let currentBatchRows = [];

    // Elements
    const sliders = {
        rpm: document.getElementById("slider_rpm"),
        oil_press: document.getElementById("slider_oil_press"),
        fuel_press: document.getElementById("slider_fuel_press"),
        coolant_press: document.getElementById("slider_coolant_press"),
        oil_temp: document.getElementById("slider_oil_temp"),
        coolant_temp: document.getElementById("slider_coolant_temp")
    };

    const valDisplays = {
        rpm: document.getElementById("val_rpm"),
        oil_press: document.getElementById("val_oil_press"),
        fuel_press: document.getElementById("val_fuel_press"),
        coolant_press: document.getElementById("val_coolant_press"),
        oil_temp: document.getElementById("val_oil_temp"),
        coolant_temp: document.getElementById("val_coolant_temp")
    };

    const analyzeBtn = document.getElementById("analyzeBtn");
    const resetBtn = document.getElementById("resetBtn");
    const presetContainer = document.getElementById("presetContainer");

    // Initialize tabs
    initTabs();

    // Initialize slider listeners
    initSliders();

    // Load presets and dataset statistics
    loadPresets();
    loadDatasetStats();

    // Run initial analysis
    runPrediction();

    // Event listeners
    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", () => {
            runPrediction();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            resetToMedians();
        });
    }

    // Initialize Batch Upload
    initBatchUpload();

    /* -------------------------------------------------------------
       Tab Switching Logic
    ------------------------------------------------------------- */
    function initTabs() {
        const tabBtns = document.querySelectorAll(".tab-btn");
        const tabContents = document.querySelectorAll(".tab-content");

        tabBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                const targetId = btn.getAttribute("data-tab");
                tabBtns.forEach(b => b.classList.remove("active"));
                tabContents.forEach(c => c.classList.remove("active"));

                btn.classList.add("active");
                const targetContent = document.getElementById(targetId);
                if (targetContent) {
                    targetContent.classList.add("active");
                }
            });
        });
    }

    /* -------------------------------------------------------------
       Sliders and Value Binding
    ------------------------------------------------------------- */
    function initSliders() {
        Object.keys(sliders).forEach(key => {
            const slider = sliders[key];
            const display = valDisplays[key];
            if (slider && display) {
                slider.addEventListener("input", (e) => {
                    display.textContent = e.target.value;
                });
            }
        });
    }

    function resetToMedians() {
        const defaults = {
            rpm: 746,
            oil_press: 3.16,
            fuel_press: 6.20,
            coolant_press: 2.17,
            oil_temp: 76.8,
            coolant_temp: 78.3
        };

        Object.keys(defaults).forEach(k => {
            if (sliders[k]) {
                sliders[k].value = defaults[k];
                if (valDisplays[k]) valDisplays[k].textContent = defaults[k];
            }
        });

        // Clear preset selection highlight
        document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("active"));
        runPrediction();
    }

    /* -------------------------------------------------------------
       Load Presets from API
    ------------------------------------------------------------- */
    async function loadPresets() {
        try {
            const res = await fetch("/api/presets");
            const presets = await res.json();
            if (!presetContainer) return;

            presetContainer.innerHTML = "";
            presets.forEach((p, idx) => {
                const card = document.createElement("div");
                card.className = `preset-card ${idx === 0 ? "active" : ""}`;
                card.innerHTML = `
                    <h4><i class="fa-solid fa-play"></i> ${p.name}</h4>
                    <p>${p.description}</p>
                `;
                card.addEventListener("click", () => {
                    document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("active"));
                    card.classList.add("active");
                    applyPreset(p.data);
                });
                presetContainer.appendChild(card);
            });
        } catch (err) {
            console.error("Failed to load presets:", err);
        }
    }

    function applyPreset(data) {
        if (data["Engine rpm"] !== undefined) {
            sliders.rpm.value = data["Engine rpm"];
            valDisplays.rpm.textContent = data["Engine rpm"];
        }
        if (data["Lub oil pressure"] !== undefined) {
            sliders.oil_press.value = data["Lub oil pressure"];
            valDisplays.oil_press.textContent = data["Lub oil pressure"];
        }
        if (data["Fuel pressure"] !== undefined) {
            sliders.fuel_press.value = data["Fuel pressure"];
            valDisplays.fuel_press.textContent = data["Fuel pressure"];
        }
        if (data["Coolant pressure"] !== undefined) {
            sliders.coolant_press.value = data["Coolant pressure"];
            valDisplays.coolant_press.textContent = data["Coolant pressure"];
        }
        if (data["lub oil temp"] !== undefined) {
            sliders.oil_temp.value = data["lub oil temp"];
            valDisplays.oil_temp.textContent = data["lub oil temp"];
        }
        if (data["Coolant temp"] !== undefined) {
            sliders.coolant_temp.value = data["Coolant temp"];
            valDisplays.coolant_temp.textContent = data["Coolant temp"];
        }

        runPrediction();
    }

    /* -------------------------------------------------------------
       Run Real-Time Prediction API
    ------------------------------------------------------------- */
    async function runPrediction() {
        const payload = {
            bike_model: document.getElementById("bikeModel")?.value || "Motorcycle",
            bike_year: parseInt(document.getElementById("bikeYear")?.value) || 2023,
            "Engine rpm": parseFloat(sliders.rpm.value),
            "Lub oil pressure": parseFloat(sliders.oil_press.value),
            "Fuel pressure": parseFloat(sliders.fuel_press.value),
            "Coolant pressure": parseFloat(sliders.coolant_press.value),
            "lub oil temp": parseFloat(sliders.oil_temp.value),
            "Coolant temp": parseFloat(sliders.coolant_temp.value)
        };

        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...`;
        }

        try {
            const res = await fetch("/api/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                throw new Error(`HTTP error ${res.status}`);
            }

            const data = await res.json();
            renderResults(data);

        } catch (err) {
            console.error("Prediction error:", err);
            alert("Prediction failed: " + err.message);
        } finally {
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = `<i class="fa-solid fa-magnifying-glass-chart"></i> Run Diagnostic Assessment`;
            }
        }
    }

    /* -------------------------------------------------------------
       Render Prediction Results
    ------------------------------------------------------------- */
    function renderResults(data) {
        // Timestamp
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        document.getElementById("timestampBadge").innerHTML = `<i class="fa-regular fa-clock"></i> Evaluated at ${timeStr}`;

        // Hero card
        const hero = document.getElementById("heroResult");
        const heroIcon = document.getElementById("heroIcon");
        const badge = document.getElementById("conditionBadge");
        const title = document.getElementById("predictionTitle");
        const summary = document.getElementById("predictionSummary");
        const healthScore = document.getElementById("healthScore");

        if (data.is_fault) {
            hero.className = "hero-result status-fault";
            heroIcon.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i>`;
            badge.textContent = "FAULT DETECTED";
            title.textContent = "Engine Condition: Fault Imminent (1)";
        } else {
            hero.className = "hero-result status-normal";
            heroIcon.innerHTML = `<i class="fa-solid fa-shield-halved"></i>`;
            badge.textContent = "HEALTHY & OPTIMAL";
            title.textContent = "Engine Condition: Normal (0)";
        }

        summary.textContent = data.summary;
        healthScore.textContent = `${data.health_score}%`;

        // Metrics grid
        document.getElementById("probNormal").textContent = `${data.probabilities.normal_pct}%`;
        document.getElementById("probFault").textContent = `${data.probabilities.fault_pct}%`;
        document.getElementById("barNormal").style.width = `${data.probabilities.normal_pct}%`;
        document.getElementById("barFault").style.width = `${data.probabilities.fault_pct}%`;

        // Risk Pill
        const riskLevelEl = document.getElementById("riskLevel");
        const riskSub = document.getElementById("riskSub");
        let pillClass = "pill-low";
        if (data.risk.level === "MODERATE") pillClass = "pill-moderate";
        if (data.risk.level === "HIGH") pillClass = "pill-high";
        if (data.risk.level === "CRITICAL") pillClass = "pill-critical";
        riskLevelEl.innerHTML = `<span class="risk-pill ${pillClass}">${data.risk.level}</span>`;
        riskSub.textContent = data.risk.label;

        // RPM Display
        const rpmVal = sliders.rpm.value;
        document.getElementById("metricRPM").textContent = `${rpmVal} rpm`;

        // Render Telemetry Breakdown Table
        renderTelemetryTable(data.sensors);

        // Render Recommendations
        renderRecommendations(data.recommendations);

        // Update Charts
        updateCharts(data);
    }

    /* -------------------------------------------------------------
       Telemetry Table Rendering
    ------------------------------------------------------------- */
    function renderTelemetryTable(sensors) {
        const tbody = document.querySelector("#sensorTable tbody");
        if (!tbody) return;
        tbody.innerHTML = "";

        const units = {
            "Engine rpm": "rpm",
            "Lub oil pressure": "bar",
            "Fuel pressure": "bar",
            "Coolant pressure": "bar",
            "lub oil temp": "°C",
            "Coolant temp": "°C"
        };

        Object.keys(sensors).forEach(sensorName => {
            const s = sensors[sensorName];
            const unit = units[sensorName] || "";
            const row = document.createElement("tr");

            let statusClass = "NORMAL";
            if (s.status === "WARNING") statusClass = "WARNING";
            if (s.status === "CRITICAL") statusClass = "CRITICAL";

            row.innerHTML = `
                <td><strong>${sensorName}</strong></td>
                <td><span class="val-mono">${s.value.toFixed(2)} ${unit}</span></td>
                <td><span class="text-dim">${s.stats.median.toFixed(2)} ${unit}</span></td>
                <td><span class="status-tag ${statusClass}">${s.status}</span></td>
                <td><small>${s.message}</small></td>
            `;
            tbody.appendChild(row);
        });
    }

    /* -------------------------------------------------------------
       Recommendations List Rendering
    ------------------------------------------------------------- */
    function renderRecommendations(recs) {
        const list = document.getElementById("recommendationList");
        if (!list) return;
        list.innerHTML = "";

        recs.forEach(r => {
            const li = document.createElement("li");
            let icon = `<i class="fa-solid fa-circle-check text-success"></i>`;
            if (r.toLowerCase().includes("immediate") || r.toLowerCase().includes("critical")) {
                icon = `<i class="fa-solid fa-triangle-exclamation text-danger"></i>`;
            } else if (r.toLowerCase().includes("monitor") || r.toLowerCase().includes("warning")) {
                icon = `<i class="fa-solid fa-circle-exclamation text-warning"></i>`;
            }
            li.innerHTML = `${icon} <span>${r}</span>`;
            list.appendChild(li);
        });
    }

    /* -------------------------------------------------------------
       Chart.js Visualizations
    ------------------------------------------------------------- */
    function updateCharts(data) {
        // Probability Distribution Bar Chart
        const probCtx = document.getElementById("probChart");
        if (probCtx) {
            const normal = data.probabilities.normal_pct;
            const fault = data.probabilities.fault_pct;

            if (probChartInstance) {
                probChartInstance.data.datasets[0].data = [normal, fault];
                probChartInstance.update();
            } else {
                probChartInstance = new Chart(probCtx, {
                    type: "bar",
                    data: {
                        labels: ["Normal (Healthy)", "Fault Detected"],
                        datasets: [{
                            data: [normal, fault],
                            backgroundColor: ["#10b981", "#ef4444"],
                            borderRadius: 6,
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => `${ctx.parsed.y.toFixed(1)}%`
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                ticks: {
                                    color: "#94a3b8",
                                    callback: (v) => `${v}%`
                                },
                                grid: { color: "rgba(255,255,255,0.06)" }
                            },
                            x: {
                                ticks: { color: "#e2e8f0", font: { weight: "600" } },
                                grid: { display: false }
                            }
                        }
                    }
                });
            }
        }

        // Radar Chart: Relative sensor load compared to reference maximum
        const radarCtx = document.getElementById("radarChart");
        if (radarCtx && data.sensors) {
            const labels = [];
            const values = [];

            Object.keys(data.sensors).forEach(feat => {
                const s = data.sensors[feat];
                labels.push(feat.replace("Engine ", "").replace("Lub ", "").replace("Coolant ", "C-"));
                // Normalize roughly (0 to 100 relative to max)
                const max = s.stats.max || 100;
                const pct = Math.min(100, Math.max(0, (s.value / max) * 100));
                values.push(Math.round(pct));
            });

            if (radarChartInstance) {
                radarChartInstance.data.labels = labels;
                radarChartInstance.data.datasets[0].data = values;
                radarChartInstance.update();
            } else {
                radarChartInstance = new Chart(radarCtx, {
                    type: "radar",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "Sensor Intensity (%)",
                            data: values,
                            backgroundColor: "rgba(56, 189, 248, 0.2)",
                            borderColor: "#38bdf8",
                            pointBackgroundColor: "#38bdf8",
                            pointBorderColor: "#fff",
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            r: {
                                angleLines: { color: "rgba(255,255,255,0.08)" },
                                grid: { color: "rgba(255,255,255,0.08)" },
                                pointLabels: { color: "#94a3b8", font: { size: 10 } },
                                ticks: { display: false, min: 0, max: 100 }
                            }
                        }
                    }
                });
            }
        }
    }

    /* -------------------------------------------------------------
       Batch CSV Diagnostics
    ------------------------------------------------------------- */
    function initBatchUpload() {
        const dropZone = document.getElementById("dropZone");
        const fileInput = document.getElementById("batchFileInput");
        const progress = document.getElementById("batchProgress");
        const summary = document.getElementById("batchSummarySection");
        const downloadBtn = document.getElementById("downloadResultsBtn");

        if (!dropZone || !fileInput) return;

        dropZone.addEventListener("click", () => fileInput.click());

        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("dragover");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            if (e.dataTransfer.files.length) {
                handleBatchFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length) {
                handleBatchFile(e.target.files[0]);
            }
        });

        async function handleBatchFile(file) {
            if (!file.name.endsWith(".csv")) {
                alert("Please select a valid CSV file.");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);

            progress.style.display = "flex";
            summary.style.display = "none";

            try {
                const res = await fetch("/api/batch-predict", {
                    method: "POST",
                    body: formData
                });

                const json = await res.json();
                if (!res.ok) {
                    throw new Error(json.error || `HTTP error ${res.status}`);
                }

                currentBatchRows = json.rows || [];
                renderBatchSummary(json);

            } catch (err) {
                console.error("Batch upload failed:", err);
                alert("Batch analysis error: " + err.message);
            } finally {
                progress.style.display = "none";
            }
        }

        function renderBatchSummary(data) {
            summary.style.display = "block";
            document.getElementById("bTotal").textContent = data.total_rows.toLocaleString();
            document.getElementById("bNormal").textContent = data.normal_count.toLocaleString();
            document.getElementById("bFault").textContent = data.fault_count.toLocaleString();
            document.getElementById("bRate").textContent = `${data.fault_rate_pct}%`;

            const tbody = document.querySelector("#batchResultTable tbody");
            tbody.innerHTML = "";

            data.rows.forEach(r => {
                const tr = document.createElement("tr");
                const isFault = (r.status === "FAULT");
                tr.innerHTML = `
                    <td>${r.id}</td>
                    <td>${r["Engine rpm"]}</td>
                    <td>${r["Lub oil pressure"]}</td>
                    <td>${r["Fuel pressure"]}</td>
                    <td>${r["Coolant pressure"]}</td>
                    <td>${r["lub oil temp"]}</td>
                    <td>${r["Coolant temp"]}</td>
                    <td><span class="status-tag ${isFault ? 'CRITICAL' : 'NORMAL'}">${r.status}</span></td>
                    <td class="${isFault ? 'text-danger' : 'text-success'}">${r.fault_prob}%</td>
                    <td><strong>${r.health_score}%</strong></td>
                `;
                tbody.appendChild(tr);
            });
        }

        if (downloadBtn) {
            downloadBtn.addEventListener("click", () => {
                if (!currentBatchRows.length) return;
                exportBatchCSV(currentBatchRows);
            });
        }

        function exportBatchCSV(rows) {
            const headers = Object.keys(rows[0]);
            const csvRows = [headers.join(",")];

            rows.forEach(r => {
                const vals = headers.map(h => r[h]);
                csvRows.push(vals.join(","));
            });

            const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `motocare_diagnostic_results_${Date.now()}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        }
    }

    /* -------------------------------------------------------------
       Dataset Stats Table
    ------------------------------------------------------------- */
    async function loadDatasetStats() {
        try {
            const res = await fetch("/api/stats");
            const stats = await res.json();
            const tbody = document.querySelector("#datasetStatsTable tbody");
            if (!tbody) return;

            tbody.innerHTML = "";
            Object.keys(stats).forEach(col => {
                const s = stats[col];
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${col}</td>
                    <td>${s.min}</td>
                    <td>${s.p25}</td>
                    <td><strong>${s.median}</strong></td>
                    <td>${s.mean}</td>
                    <td>${s.p75}</td>
                    <td>${s.max}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (err) {
            console.error("Failed to load dataset stats:", err);
        }
    }
});
