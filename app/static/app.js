const qs = (sel) => document.querySelector(sel);

function showError(msg) {
  const el = qs("#form-error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

function clearError() {
  const el = qs("#form-error");
  el.textContent = "";
  el.classList.add("hidden");
}

function renderResult(payload) {
  const section = qs("#result-section");
  const body = qs("#result-body");
  const rec = payload.record;
  const wx = payload.weather || {};
  const map = wx.map_link
    ? `<div class="metric map-link"><div class="k">Map</div><div class="v"><a href="${wx.map_link}" target="_blank" rel="noopener">Open in OpenStreetMap</a></div></div>`
    : "";

  body.innerHTML = `
    <div class="metric full">
      <div class="k">Resolved location</div>
      <div class="v">${rec.resolved_location_name}</div>
      <div class="muted">${rec.latitude.toFixed(4)}, ${rec.longitude.toFixed(4)}</div>
    </div>
    ${map}
    <div class="metric"><div class="k">Condition</div><div class="v">${wx.weather_summary || "—"}</div></div>
    <div class="metric"><div class="k">Temperature</div><div class="v">${formatNum(wx.temperature_c)}°C</div></div>
    <div class="metric"><div class="k">Feels like</div><div class="v">${formatNum(wx.apparent_temperature_c)}°C</div></div>
    <div class="metric"><div class="k">Humidity</div><div class="v">${formatNum(wx.humidity_percent)}%</div></div>
    <div class="metric"><div class="k">Wind</div><div class="v">${formatNum(wx.wind_speed_kmh)} km/h</div></div>
    <div class="metric"><div class="k">Precip chance</div><div class="v">${formatNum(wx.precipitation_probability_percent)}%</div></div>
    <div class="metric"><div class="k">Visibility</div><div class="v">${wx.visibility_m != null ? formatNum(wx.visibility_m) + " m" : "—"}</div></div>
    <div class="metric"><div class="k">UV index</div><div class="v">${formatNum(wx.uv_index)}</div></div>
    <div class="metric"><div class="k">Sunrise</div><div class="v">${wx.sunrise || "—"}</div></div>
    <div class="metric"><div class="k">Sunset</div><div class="v">${wx.sunset || "—"}</div></div>
    <div class="metric"><div class="k">Saved record</div><div class="v">#${rec.id} (${rec.query_type})</div></div>
  `;
  section.hidden = false;
}

function formatNum(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  const n = Number(v);
  return Math.abs(n) >= 10 ? n.toFixed(1) : n.toFixed(2);
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

async function loadHistory() {
  const res = await fetch("/api/records");
  const data = await res.json();
  const list = qs("#history-list");
  const empty = qs("#history-empty");
  list.innerHTML = "";
  if (!data.success || !data.data.records.length) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");
  data.data.records.forEach((r) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.innerHTML = `
      <div>
        <strong>#${r.id} — ${r.resolved_location_name}</strong>
        <div class="history-meta">${r.query_type} · ${r.temperature_c != null ? r.temperature_c.toFixed(1) + "°C" : "n/a"}</div>
      </div>
      <div class="history-meta">${new Date(r.created_at).toLocaleString()}</div>
    `;
    li.addEventListener("click", () => {
      qs("#crud-id").value = r.id;
      qs("#crud-location").value = r.original_location_input;
      qs("#crud-start").value = r.start_date || "";
      qs("#crud-end").value = r.end_date || "";
      showCrud(`Loaded record #${r.id} into the form below.`, "success");
    });
    list.appendChild(li);
  });
}

function showCrud(msg, kind) {
  const el = qs("#crud-msg");
  el.textContent = msg;
  el.classList.remove("hidden", "error", "success");
  el.classList.add(kind === "error" ? "error" : "success");
}

function wireGeo(btnId, targetInput) {
  qs(btnId).addEventListener("click", () => {
    if (!navigator.geolocation) {
      showError("Geolocation is not available in this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const body = {
          location_input: `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
          use_current_location: true,
          latitude,
          longitude,
        };
        if (btnId === "#geo-btn") {
          qs("#location-input").value = body.location_input;
          window.__pendingGeoBody = body;
        } else {
          qs(targetInput).value = body.location_input;
          window.__crudGeoBody = body;
        }
        clearError();
      },
      () => showError("Unable to read your location. Check permissions."),
      { enableHighAccuracy: true, timeout: 15000 }
    );
  });
}

document.addEventListener("DOMContentLoaded", () => {
  qs("#weather-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();
    const location_input = qs("#location-input").value.trim();
    const start_date = qs("#start-date").value || null;
    const end_date = qs("#end-date").value || null;

    let body = {
      location_input,
      start_date,
      end_date,
      use_current_location: false,
    };

    if (window.__pendingGeoBody) {
      body = { ...window.__pendingGeoBody, start_date, end_date };
      window.__pendingGeoBody = null;
    }

    const { ok, data } = await postJson("/api/weather/query", body);
    if (!ok || !data.success) {
      const msg = data.error?.message || "Request failed.";
      showError(msg);
      return;
    }
    renderResult(data.data);
    loadHistory();
  });

  wireGeo("#geo-btn");

  qs("#refresh-history").addEventListener("click", () => loadHistory());

  wireGeo("#crud-geo", "#crud-location");

  qs("#crud-update").addEventListener("click", async () => {
    const id = Number(qs("#crud-id").value);
    if (!id) {
      showCrud("Enter a record id.", "error");
      return;
    }
    const payload = {
      location_input: qs("#crud-location").value.trim(),
      start_date: qs("#crud-start").value || null,
      end_date: qs("#crud-end").value || null,
      use_current_location: false,
    };
    if (window.__crudGeoBody) {
      Object.assign(payload, window.__crudGeoBody, {
        start_date: qs("#crud-start").value || null,
        end_date: qs("#crud-end").value || null,
      });
      window.__crudGeoBody = null;
    }
    const res = await fetch(`/api/records/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!data.success) {
      showCrud(data.error?.message || "Update failed", "error");
      return;
    }
    showCrud(`Updated record #${id}.`, "success");
    loadHistory();
  });

  qs("#crud-delete").addEventListener("click", async () => {
    const id = Number(qs("#crud-id").value);
    if (!id) {
      showCrud("Enter a record id.", "error");
      return;
    }
    if (!confirm(`Delete record #${id}? This cannot be undone.`)) return;
    const res = await fetch(`/api/records/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (!data.success) {
      showCrud(data.error?.message || "Delete failed", "error");
      return;
    }
    showCrud(`Deleted record #${id}.`, "success");
    loadHistory();
  });

  loadHistory();
});
