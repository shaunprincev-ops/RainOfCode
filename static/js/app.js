let map = null;
let marker = null;

const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function showError(msg){
  $("error").textContent = msg;
  $("error").classList.remove("hidden");
}
function severityClass(s){return s.toLowerCase().replace(" ","-")}

$("searchForm").addEventListener("submit", async e => {
  e.preventDefault();
  $("error").classList.add("hidden");
  $("loading").classList.remove("hidden");
  $("dashboard").classList.add("hidden");

  try{
    const res = await fetch("/api/analyze-flood", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({location:$("location").value,flood_date:$("floodDate").value,flood_time:$("floodTime").value})
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Analysis failed");
    render(data);
  }catch(err){showError(err.message)}
  finally{$("loading").classList.add("hidden")}
});

function render(data){
  $("dashboard").classList.remove("hidden");
  $("eventInfo").textContent = `${data.flood_date} ${data.flood_time !== "Unknown" ? data.flood_time : "(time unknown)"}`;
  $("windowInfo").textContent = `data window ${data.analysis_window.start} → ${data.analysis_window.end}`;
  $("severity").textContent = data.severity;
  $("severityScore").textContent = `Evidence score ${data.severity_score}/100`;
  $("confidence").textContent = `${data.confidence}%`;
  $("rain").textContent = data.weather.rain_24h_mm == null ? "N/A" : `${data.weather.rain_24h_mm} mm`;
  $("reports").textContent = data.news.length;

  $("areas").innerHTML = data.areas.map(a => `
    <div class="area">
      <h3>${esc(a.name)}</h3>
      <div class="row"><span>Severity</span><b>${esc(a.severity)}</b></div>
      <div class="row"><span>Water depth</span><b>${esc(a.water_depth)}</b></div>
      <div class="row"><span>Road impact</span><b>${esc(a.roads_affected)}</b></div>
      <div class="row"><span>Buildings</span><b>${esc(a.buildings_affected)}</b></div>
      <div class="row"><span>Evidence</span><b>${a.evidence} sources</b></div>
      <div class="row"><span>Confidence</span><b>${a.confidence}%</b></div>
    </div>`).join("");

  const r=data.report;
  $("report").innerHTML = `<div class="report">
    <p><b>Overview:</b> ${esc(r.overview)}</p>
    <p><b>Severity:</b> ${esc(r.severity)}</p>
    <p><b>Weather:</b> ${esc(r.weather)}</p>
    <p><b>Evidence:</b> ${esc(r.evidence)}</p>
    <p><b>Building analysis:</b> ${esc(r.building)}</p>
    <p><b>Uncertainty:</b> ${esc(r.uncertainty)}</p>
  </div>`;

  $("news").innerHTML = data.news.length ? data.news.map(n => `
    <div class="source-item">
      <strong>${esc(n.title)}</strong>
      <p>Published: ${esc(n.published || "Unknown")} · Event date: ${esc(n.event_date || "Unknown")} · Relevance: ${esc(n.temporal_relevance || "unknown")}</p>
      ${n.url ? `<a href="${esc(n.url)}" target="_blank" rel="noopener">Open source →</a>` : ""}
    </div>`).join("") : `<div class="result-box muted">No flood-related public reports were found in the feed.</div>`;

  if(!map){
    map = L.map("map").setView([data.lat,data.lon],14);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap contributors"}).addTo(map);
  }else map.setView([data.lat,data.lon],14);
  if(marker) marker.remove();
  marker=L.marker([data.lat,data.lon]).addTo(map).bindPopup(`<b>${esc(data.location)}</b><br>Severity: ${esc(data.severity)}`).openPopup();

  // Plot nearby OSM buildings lightly to make the map useful immediately.
  (data.osm.buildings || []).slice(0,60).forEach(b=>{
    if(b.lat && b.lon) L.circleMarker([b.lat,b.lon],{radius:3,weight:1,fillOpacity:.35}).addTo(map)
      .bindPopup(`<small>Mapped building<br>${esc(b.name)}</small>`);
  });

  window.scrollTo({top:$("dashboard").offsetTop-20,behavior:"smooth"});
}

$("buildingForm").addEventListener("submit", async e=>{
  e.preventDefault();
  const building=$("building").value.trim();
  if(!building) return;
  $("buildingResult").innerHTML="Checking location and location-specific evidence…";
  try{
    const res=await fetch("/api/building-analysis",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({location:$("location").value,building,flood_date:$("floodDate").value,flood_time:$("floodTime").value})});
    const d=await res.json(); if(!res.ok) throw new Error(d.error);
    $("buildingResult").innerHTML=`
      <b>${esc(d.building)}</b><br>
      <span class="muted">${esc(d.location)}</span>
      <div class="row"><span>Flood status</span><b>${esc(d.flood_status)}</b></div>
      <div class="row"><span>Ground floor</span><b>${esc(d.ground_floor)}</b></div>
      <div class="row"><span>Water depth</span><b>${esc(d.water_depth)}</b></div>
      <div class="row"><span>Visible damage</span><b>${esc(d.visible_damage)}</b></div>
      <div class="row"><span>Confidence</span><b>${d.confidence}%</b></div>
      <p>${esc(d.explanation)}</p>`;
    if(map){map.setView([d.lat,d.lon],17);L.marker([d.lat,d.lon]).addTo(map).bindPopup(`<b>${esc(d.building)}</b>`).openPopup();}
  }catch(err){$("buildingResult").textContent=err.message}
});
