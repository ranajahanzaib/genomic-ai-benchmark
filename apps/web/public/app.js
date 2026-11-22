const API = "http://127.0.0.1:8000/api";
let samples = [],
  selected = null,
  projection = [],
  lastEval = null,
  lastLeak = null;
const $ = (s) => document.querySelector(s),
  esc = (s) =>
    String(s).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
async function api(path, options = {}) {
  const r = await fetch(API + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const d = await r.json();
  if (!r.ok) {
    const detail = Array.isArray(d.detail)
      ? d.detail.map((x) => x.msg).join("; ")
      : d.detail;
    throw Error(detail || d.error || "Request failed");
  }
  return d;
}
function nav() {
  const route = location.hash.slice(1) || "overview";
  document
    .querySelectorAll(".view")
    .forEach((v) => v.classList.toggle("active", v.id === route));
  document
    .querySelectorAll("#nav a")
    .forEach((a) => a.classList.toggle("active", a.hash === "#" + route));
  $("#crumb").textContent = route
    .split("-")
    .map((s) => s[0].toUpperCase() + s.slice(1))
    .join(" ");
  if (route === "embeddings") draw();
}
function renderTables(models, datasets, runtime) {
  const modelRows = models
    .map(
      (m) =>
        `<tr><td>${esc(m.name)}</td><td>${esc(m.family)}</td><td><span class="pill warn">${esc(m.status)}</span></td></tr>`,
    )
    .join("");
  const dsRows = datasets
    .map(
      (d) =>
        `<tr><td>${esc(d.name)}</td><td>${d.record_count} records</td><td><span class="pill">${esc(d.status)}</span></td></tr>`,
    )
    .join("");
  $("#model-table").innerHTML =
    `<table class="data-table"><thead><tr><th>MODEL</th><th>FAMILY</th><th>ADAPTER STATUS</th></tr></thead><tbody>${modelRows}</tbody></table>`;
  $("#dataset-table").innerHTML =
    `<table class="data-table"><thead><tr><th>DATASET</th><th>SIZE</th><th>PROVENANCE</th></tr></thead><tbody>${dsRows}</tbody></table>`;
  const meta = JSON.parse(models[0]?.metadata_json || "{}");
  $("#models-detail").innerHTML =
    $("#model-table").innerHTML +
    `<div class="result-box"><div class="result-head"><b>Verified model metadata</b><span class="pill warn">Inference ${runtime.available ? "available" : "unavailable"}</span></div><p>Organization: ${esc(meta.organization || "unknown")} · Architecture: ${esc(meta.architecture || "unknown")} · Parameters: ${esc(meta.parameter_count || "unknown")} · Checkpoint: <span class="mono">${esc(meta.checkpoint || "unknown")}</span></p><p>Objective: ${esc(meta.training_objective || "unknown")} · Context: ${meta.max_context_bases || "unknown"} bp · Pretraining data: ${esc(meta.pretraining_data || "unknown")}</p><p>Revision: ${esc(meta.checkpoint_revision || "unknown")} · Digest: ${esc(meta.checkpoint_sha256 || "unknown")} · License: ${esc(meta.license || "unknown")}</p><p><b>Local runtime:</b> ${esc(runtime.environment.platform)} · Python ${esc(runtime.environment.python)} · CUDA ${esc(runtime.environment.cuda_version || "unavailable")}</p><p>${runtime.reasons.map(esc).join("<br>")}</p></div>`;
  $("#dataset-detail").innerHTML = $("#dataset-table").innerHTML;
  $("#point-count").textContent = samples.length;
  document.querySelectorAll(".mono").forEach((el) => {
    if (el.textContent.includes("8 records"))
      el.textContent = `${samples.length} records`;
  });
}
function project() {
  projection = samples.map((s) => {
    let gc = (s.sequence.match(/[GC]/g) || []).length / s.sequence.length,
      a = (s.sequence.match(/A/g) || []).length / s.sequence.length,
      motif = s.sequence.includes("TATAAT") ? 1 : 0;
    return {
      x: gc * 1.3 + a * 0.5 + ((s.id.charCodeAt(5) || 0) % 7) * 0.015,
      y:
        motif * 0.55 +
        (s.sequence.length % 9) * 0.025 +
        ((s.id.charCodeAt(6) || 0) % 7) * 0.014,
    };
  });
}
function draw() {
  for (const id of ["plot", "plot2"]) {
    const c = document.getElementById(id);
    if (!c) continue;
    const rect = c.getBoundingClientRect(),
      dpr = devicePixelRatio || 1;
    c.width = rect.width * dpr;
    c.height = rect.height * dpr;
    const ctx = c.getContext("2d");
    ctx.scale(dpr, dpr);
    const w = rect.width,
      h = rect.height,
      pad = 25;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = getComputedStyle(document.body).getPropertyValue(
      "--line",
    );
    ctx.lineWidth = 1;
    for (let i = 0; i < 4; i++) {
      let y = pad + (i * (h - 2 * pad)) / 3;
      ctx.beginPath();
      ctx.moveTo(pad, y);
      ctx.lineTo(w - 8, y);
      ctx.stroke();
    }
    ctx.fillStyle = "#87918f";
    ctx.font = "9px DM Mono";
    ctx.fillText("GC fraction →", w - 93, h - 5);
    projection.forEach((p, i) => {
      let x = pad + p.x * (w - 2 * pad),
        y = h - pad - p.y * (h - 2 * pad);
      const s = samples[i],
        bySpecies = $("#colorby")?.selectedIndex === 1;
      ctx.beginPath();
      ctx.arc(x, y, s === selected ? 7 : 5, 0, Math.PI * 2);
      ctx.fillStyle = bySpecies
        ? ["#4576cb", "#d77b63", "#34856c", "#b18b49", "#8069b4"][i % 5]
        : s.label === "motif-present"
          ? "#4576cb"
          : "#dc8a71";
      ctx.globalAlpha = 0.83;
      ctx.fill();
      ctx.globalAlpha = 1;
      if (s === selected) {
        ctx.strokeStyle = "#202a39";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });
    c.onclick = (e) => {
      let r = c.getBoundingClientRect(),
        x = e.clientX - r.left,
        y = e.clientY - r.top;
      let idx = projection
        .map((p, i) => ({
          i,
          x: pad + p.x * (r.width - 2 * pad),
          y: r.height - pad - p.y * (r.height - 2 * pad),
        }))
        .sort(
          (a, b) => Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y),
        )[0];
      if (idx && Math.hypot(idx.x - x, idx.y - y) < 22) {
        selected = samples[idx.i];
        updateSelection();
        draw();
      }
    };
  }
}
function updateSelection() {
  if (!selected) return;
  $("#selected").innerHTML =
    `<b>${esc(selected.id)}</b> · ${esc(selected.species)} · ${esc(selected.label)} <span class="mono">${selected.sequence.length} bp</span>`;
  $("#seq-name").textContent =
    selected.id + " · " + selected.species + " · " + selected.label;
  $("#seq-length").textContent = selected.sequence.length + " bp";
  $("#bases").innerHTML = [...selected.sequence]
    .map((b, i) =>
      i % 10 === 0
        ? ` <span class="base-${b.toLowerCase()}">${b}</span>`
        : `<span class="base-${b.toLowerCase()}">${b}</span>`,
    )
    .join("");
  let nums = [];
  for (let i = 1; i <= selected.sequence.length; i += 10) nums.push(i);
  $("#seq-ruler").textContent = nums.join("          ");
}
async function load() {
  try {
    const [overview, models, datasets, seqs, runs, runtime] = await Promise.all(
      [
        "/overview",
        "/models",
        "/datasets",
        "/sequences",
        "/runs",
        "/models/evo2/status",
      ].map(api),
    );
    $("#s-models").textContent = overview.models;
    $("#s-datasets").textContent = overview.datasets;
    $("#s-sequences").textContent = overview.sequences;
    $("#s-runs").textContent = overview.runs;
    samples = seqs;
    project();
    renderTables(models, datasets, runtime);
    if (runs.length) {
      const last = JSON.parse(runs[0].result_json);
      if (runs[0].kind === "grouped-baseline") showEval(last);
      if (runs[0].kind === "leakage-audit") showLeak(last);
    }
    $("#run-table").innerHTML = runs.length
      ? `<table class="data-table"><thead><tr><th>RUN</th><th>KIND</th><th>STATUS</th><th>CREATED</th></tr></thead><tbody>${runs.map((r) => `<tr><td>#${r.id}</td><td>${esc(r.kind)}</td><td>${esc(r.status)}</td><td>${esc(r.created_at)}</td></tr>`).join("")}</tbody></table>`
      : '<p class="muted">No runs yet. Start an evaluation or leakage audit.</p>';
    draw();
  } catch (e) {
    $(".badge").innerHTML = "API DISCONNECTED";
    $(".badge").style.color = "#b95347";
    console.error(e);
  }
}
function showEval(r) {
  lastEval = r;
  const interval = r.accuracy_cluster_bootstrap_95
    ? `${(r.accuracy_cluster_bootstrap_95[0] * 100).toFixed(1)}–${(r.accuracy_cluster_bootstrap_95[1] * 100).toFixed(1)}%`
    : "not estimated";
  $("#eval-summary").innerHTML =
    r.status === "completed"
      ? `<div class="metric">${(r.accuracy * 100).toFixed(1)}%</div><p>${r.n} held-out records · species-cluster interval ${interval}</p><button class="text-button" onclick="location.hash='benchmarks'">View predictions →</button>`
      : `<p>${esc(r.reason)}</p>`;
  $("#eval-detail").innerHTML =
    `<div class="result-box"><div class="result-head"><b>Grouped baseline result</b><span><button class="text-button" data-export="evaluation">Export JSON ↓</button> <span class="metric">${r.accuracy == null ? "—" : (r.accuracy * 100).toFixed(1) + "%"}</span></span></div><p>Method: ${esc(r.method || "—")} · Split: ${esc(r.split || "—")} · Evaluated records: ${r.n || 0} · Data status: synthetic fixture</p><p>95% species-cluster bootstrap interval: ${interval} · ${esc(r.uncertainty_note || "")}<br>Balanced accuracy: ${r.balanced_accuracy == null ? "—" : (r.balanced_accuracy * 100).toFixed(1) + "%"} · Macro F1: ${r.macro_f1 == null ? "—" : r.macro_f1.toFixed(3)}</p>${r.reason ? `<p>${esc(r.reason)}</p>` : ""}${r.predictions?.length ? `<table class="data-table"><thead><tr><th>RECORD</th><th>HELD-OUT SPECIES</th><th>TRUTH</th><th>PREDICTION</th></tr></thead><tbody>${r.predictions.map((p) => `<tr><td>${esc(p.id)}</td><td>${esc(p.species)}</td><td>${esc(p.truth)}</td><td>${esc(p.prediction)}</td></tr>`).join("")}</tbody></table>` : ""}</div>`;
}
function showLeak(r) {
  lastLeak = r;
  $("#leak-count").textContent = r.hit_count;
  $("#leak-detail").innerHTML =
    `<div class="result-box"><div class="result-head"><b>Overlap evidence</b><span><button class="text-button" data-export="leakage">Export JSON ↓</button> <span class="metric">${r.hit_count}</span></span></div><p>${esc(r.method)}. Coverage: ${esc(r.corpus_coverage)}.</p>${r.hits.length ? `<table class="data-table"><thead><tr><th>LEFT</th><th>RIGHT</th><th>TYPE</th><th>SPLITS</th></tr></thead><tbody>${r.hits.map((h) => `<tr><td>${esc(h.left)}</td><td>${esc(h.right)}</td><td>${esc(h.kind)}</td><td>${esc(h.left_split)} → ${esc(h.right_split)}</td></tr>`).join("")}</tbody></table>` : "<p>No matching sequence pairs were detected in the indexed fixture.</p>"}</div>`;
}
document.addEventListener("click", async (e) => {
  const exported = e.target.closest("[data-export]")?.dataset.export;
  if (exported) {
    const result = exported === "evaluation" ? lastEval : lastLeak;
    if (result) {
      const manifest = {
        manifest_version: 1,
        created_at: new Date().toISOString(),
        data_status: "synthetic fixture",
        result,
      };
      const blob = new Blob([JSON.stringify(manifest, null, 2)], {
          type: "application/json",
        }),
        url = URL.createObjectURL(blob),
        a = document.createElement("a");
      a.href = url;
      a.download = `genomic-ai-${exported}-run-${result.run_id || "local"}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
    return;
  }
  const action = e.target.closest("[data-action]")?.dataset.action;
  if (!action) return;
  try {
    if (action === "validate") {
      const result = await api("/splits/validate");
      $("#split-detail").innerHTML =
        `<div class="result-box"><div class="result-head"><b>Declared split validation</b><span class="metric">${result.species_crossing_count} group crossings</span></div><p>${esc(result.scope)}</p>${result.species_crossings.length ? `<table class="data-table"><thead><tr><th>SPECIES</th><th>SPLITS</th></tr></thead><tbody>${result.species_crossings.map((x) => `<tr><td>${esc(x.species)}</td><td>${esc(x.splits.join(", "))}</td></tr>`).join("")}</tbody></table>` : "<p>No species is assigned to multiple declared splits in this fixture.</p>"}</div>`;
      return;
    }
    const result = await api(
      "/" + (action === "evaluate" ? "evaluate" : "leakage"),
      { method: "POST", body: "{}" },
    );
    if (action === "evaluate") showEval(result);
    else showLeak(result);
    await load();
  } catch (err) {
    alert(err.message);
  }
});
$("#import-btn").onclick = async () => {
  try {
    const r = await api("/import/fasta", {
      method: "POST",
      body: JSON.stringify({
        name: $("#dataset-name").value,
        fasta: $("#fasta").value,
      }),
    });
    $("#import-message").textContent =
      `Imported ${r.records} sequences · ${r.data_status}`;
    await load();
  } catch (e) {
    $("#import-message").textContent = "Import error: " + e.message;
  }
};
$("#ncbi-import-btn").onclick = async () => {
  try {
    $("#ncbi-message").textContent = "Retrieving versioned record from NCBI…";
    const r = await api("/import/ncbi", {
      method: "POST",
      body: JSON.stringify({ accession: $("#ncbi-accession").value }),
    });
    $("#ncbi-message").textContent =
      `Imported ${r.accession_version} · SHA-256 ${r.fasta_sha256.slice(0, 16)}… · metadata recorded.`;
    await load();
  } catch (e) {
    $("#ncbi-message").textContent = "Retrieval error: " + e.message;
  }
};
$("#theme").onclick = () => document.body.classList.toggle("dark");
$("#colorby").onchange = draw;
$("#reset-points").onclick = () => {
  selected = null;
  draw();
};
window.addEventListener("hashchange", nav);
window.addEventListener("resize", draw);
nav();
load();
