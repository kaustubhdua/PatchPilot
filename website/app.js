const SAMPLE_DIFF = `diff --git a/src/auth.py b/src/auth.py
index 11aa111..22bb222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,5 +1,6 @@
 import os
+import subprocess
 
 def authenticate(token):
-    return validate_token(token)
+    os.system("echo validating")
+    return validate_token(token)
`;
const $ = (id) => document.getElementById(id);
const diffInput = $("diff-input");
const apiInput = $("api-url");
if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") apiInput.value = window.location.origin;
const analyzeButton = $("analyze-button");
const statusMessage = $("status-message");
const charCount = $("char-count");
$("year").textContent = new Date().getFullYear();
function setStatus(message, kind = "") { statusMessage.textContent = message; statusMessage.className = `status-message ${kind}`; }
function updateCount() { charCount.textContent = `${diffInput.value.length.toLocaleString()} characters`; }
diffInput.addEventListener("input", updateCount);
$("load-sample").addEventListener("click", () => { diffInput.value = SAMPLE_DIFF; updateCount(); setStatus("Sample loaded. Connect to your PatchPilot API to analyze it."); });
function safeText(tag, className, text) { const node = document.createElement(tag); if (className) node.className = className; node.textContent = text ?? ""; return node; }
function appendFinding(finding) {
  const card = safeText("article", "finding", "");
  const head = safeText("div", "finding-head", "");
  head.append(safeText("span", `severity ${String(finding.severity || "").toLowerCase()}`, String(finding.severity || "info").toUpperCase()));
  head.append(safeText("span", "rule-id", finding.rule_id || "RULE"));
  head.append(safeText("span", "", finding.title || "Finding"));
  card.append(head);
  if (finding.detail) card.append(safeText("p", "", finding.detail));
  if (Array.isArray(finding.evidence) && finding.evidence.length) {
    const evidence = safeText("div", "evidence", `Evidence: ${finding.evidence.slice(0, 3).join(" · ")}`);
    card.append(evidence);
  }
  $("finding-list").append(card);
}
function renderReport(data) {
  $("empty-state").classList.add("hidden"); $("report").classList.remove("hidden");
  $("report-state").textContent = "ANALYSIS COMPLETE";
  $("risk-score").textContent = data.risk_score ?? "—";
  const level = String(data.risk_level || "unknown").toLowerCase();
  $("risk-level").textContent = level; $("risk-level").className = `risk-badge ${level}`;
  $("report-summary").textContent = data.summary || "Analysis finished.";
  $("files-count").textContent = data.files_changed ?? data.files?.length ?? 0;
  $("additions-count").textContent = data.additions ?? 0; $("deletions-count").textContent = data.deletions ?? 0;
  $("file-count-label").textContent = String((data.files || []).length);
  $("file-list").replaceChildren();
  for (const file of (data.files || [])) {
    const row = safeText("div", "file-row", "");
    row.append(safeText("span", "", file.path || "(unknown path)"));
    const stats = safeText("span", "file-stats", "");
    stats.append(safeText("span", "plus", `+${file.additions ?? 0}`), document.createTextNode(" / "), safeText("span", "minus", `−${file.deletions ?? 0}`));
    row.append(stats); $("file-list").append(row);
  }
  $("finding-count").textContent = String((data.findings || []).length);
  $("finding-list").replaceChildren();
  if (!(data.findings || []).length) $("finding-list").append(safeText("p", "no-findings", "No findings triggered. This is not proof that the change is safe."));
  else for (const finding of data.findings) appendFinding(finding);
  $("test-list").replaceChildren();
  for (const item of (data.recommended_tests || [])) $("test-list").append(safeText("li", "", item));
  $("disclaimer").textContent = data.disclaimer || "Heuristic triage only; not a security audit or merge recommendation.";
}
async function checkConnection() {
  const base = apiInput.value.trim().replace(/\/$/, "");
  if (!base) throw new Error("Enter an API base URL first.");
  const response = await fetch(`${base}/health`, {headers: {Accept: "application/json"}});
  if (!response.ok) throw new Error(`Health check returned HTTP ${response.status}.`);
  return base;
}
$("check-api").addEventListener("click", async () => {
  setStatus("Checking API connection…");
  try { const base = await checkConnection(); setStatus(`Connected to ${base}`, "success"); }
  catch (error) { setStatus(`Could not connect: ${error.message}. Check the URL and CORS configuration.`, "error"); }
});
analyzeButton.addEventListener("click", async () => {
  const diff = diffInput.value;
  if (!diff.trim()) { setStatus("Paste a unified diff or load the sample first.", "error"); diffInput.focus(); return; }
  if (diff.length > 500000) { setStatus("The diff exceeds the 500,000-character API limit.", "error"); return; }
  let base;
  try { base = await checkConnection(); }
  catch (error) { setStatus(`API connection failed: ${error.message}. Start the API locally or enter a reachable API URL.`, "error"); return; }
  analyzeButton.disabled = true; analyzeButton.querySelector("span").textContent = "Analyzing…";
  $("report-state").textContent = "ANALYZING";
  setStatus("Sending diff to the configured API…");
  try {
    const response = await fetch(`${base}/v1/analyze`, {method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify({title:"Website diff analysis",base_ref:"base",head_ref:"head",diff})});
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail ? JSON.stringify(payload.detail) : `API returned HTTP ${response.status}`);
    renderReport(payload); setStatus("Analysis complete. Review the evidence and verify findings yourself.", "success");
  } catch (error) {
    $("report-state").textContent = "ANALYSIS FAILED";
    setStatus(`Analysis failed: ${error.message}. If this is a browser CORS error, configure the API to allow this website's origin.`, "error");
  } finally { analyzeButton.disabled = false; analyzeButton.querySelector("span").textContent = "Analyze diff"; }
});
updateCount();