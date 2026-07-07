const API = "/api/v1";
const OTP_LENGTH = 6;
const RESEND_COOLDOWN_SECONDS = 60;

// ---------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------
function initTheme() {
  const saved = window.__theme || "light";
  document.documentElement.setAttribute("data-theme", saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  window.__theme = next;
}

// ---------------------------------------------------------------------
// In-memory session (kept in JS memory only — no browser storage APIs
// are used, per this environment's constraints).
// ---------------------------------------------------------------------
const session = { accessToken: null, refreshToken: null, user: null };

// Transient state for in-flight registration / forgot-password flows.
const flow = { registerEmail: null, forgotEmail: null, resetToken: null };

// ---------------------------------------------------------------------
// Toasts
// ---------------------------------------------------------------------
function toast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ---------------------------------------------------------------------
// API helper
// ---------------------------------------------------------------------
async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  if (session.accessToken) {
    headers["Authorization"] = `Bearer ${session.accessToken}`;
  }
  const resp = await fetch(`${API}${path}`, { ...options, headers });
  let body = null;
  try { body = await resp.json(); } catch { /* no body */ }

  if (!resp.ok) {
    const message = (body && (body.message || body.detail)) || `Request failed (${resp.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return body;
}

// ---------------------------------------------------------------------
// Password strength
// ---------------------------------------------------------------------
function passwordChecks(password) {
  return {
    min_length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

function updatePasswordUI(password, fillEl, checklistEl) {
  const checks = passwordChecks(password);
  const metCount = Object.values(checks).filter(Boolean).length;

  checklistEl.querySelectorAll("li").forEach((li) => {
    const rule = li.dataset.rule;
    li.classList.toggle("met", !!checks[rule]);
  });

  const pct = (metCount / 5) * 100;
  fillEl.style.width = `${pct}%`;
  fillEl.classList.remove("weak", "fair", "strong");
  if (metCount <= 2) fillEl.classList.add("weak");
  else if (metCount <= 4) fillEl.classList.add("fair");
  else fillEl.classList.add("strong");

  return checks;
}

function isPasswordValid(password) {
  return Object.values(passwordChecks(password)).every(Boolean);
}

// ---------------------------------------------------------------------
// OTP input boxes
// ---------------------------------------------------------------------
function buildOtpBoxes(containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  const inputs = [];
  for (let i = 0; i < OTP_LENGTH; i++) {
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "numeric";
    input.maxLength = 1;
    input.autocomplete = "one-time-code";
    input.addEventListener("input", () => {
      input.value = input.value.replace(/[^0-9]/g, "");
      if (input.value && i < OTP_LENGTH - 1) inputs[i + 1].focus();
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !input.value && i > 0) inputs[i - 1].focus();
    });
    input.addEventListener("paste", (e) => {
      e.preventDefault();
      const text = (e.clipboardData.getData("text") || "").replace(/[^0-9]/g, "");
      text.split("").slice(0, OTP_LENGTH).forEach((ch, idx) => {
        if (inputs[idx]) inputs[idx].value = ch;
      });
      inputs[Math.min(text.length, OTP_LENGTH - 1)].focus();
    });
    inputs.push(input);
    container.appendChild(input);
  }
  inputs[0].focus();

  return {
    getCode: () => inputs.map((i) => i.value).join(""),
    clear: () => { inputs.forEach((i) => (i.value = "")); inputs[0].focus(); },
  };
}

let registerOtp = null;
let forgotOtp = null;

// ---------------------------------------------------------------------
// Resend cooldown timer
// ---------------------------------------------------------------------
function startResendCooldown(linkEl, timerEl, onResend) {
  let remaining = RESEND_COOLDOWN_SECONDS;
  linkEl.classList.add("hidden");
  timerEl.textContent = `Resend in ${remaining}s`;
  const interval = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(interval);
      timerEl.textContent = "";
      linkEl.classList.remove("hidden");
    } else {
      timerEl.textContent = `Resend in ${remaining}s`;
    }
  }, 1000);
  linkEl.onclick = async (e) => {
    e.preventDefault();
    try {
      await onResend();
      toast("A new code has been sent.", "success");
      startResendCooldown(linkEl, timerEl, onResend);
    } catch (err) {
      toast(err.message, "error");
    }
  };
}

// ---------------------------------------------------------------------
// Auth: step visibility
// ---------------------------------------------------------------------
const AUTH_STEPS = [
  "authTabs", "loginForm", "registerForm", "registerOtpStep",
  "forgotEmailStep", "forgotOtpStep", "forgotNewPasswordStep",
];

function showAuthStep(...visibleIds) {
  AUTH_STEPS.forEach((id) => {
    document.getElementById(id).classList.toggle("hidden", !visibleIds.includes(id));
  });
}

function showLogin() {
  showAuthStep("authTabs", "loginForm");
  document.getElementById("tabLogin").classList.add("active");
  document.getElementById("tabRegister").classList.remove("active");
}
function showRegister() {
  showAuthStep("authTabs", "registerForm");
  document.getElementById("tabLogin").classList.remove("active");
  document.getElementById("tabRegister").classList.add("active");
}

// ---------------------------------------------------------------------
// Auth: registration (Feature 1 — Email OTP)
// ---------------------------------------------------------------------
async function requestRegisterOtp() {
  const first_name = document.getElementById("registerFirstName").value.trim();
  const last_name = document.getElementById("registerLastName").value.trim();
  const username = document.getElementById("registerUsername").value.trim();
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value;
  const confirm_password = document.getElementById("registerConfirmPassword").value;

  if (!isPasswordValid(password)) {
    toast("Password does not meet all requirements.", "error");
    return;
  }
  if (password !== confirm_password) {
    toast("Passwords do not match.", "error");
    return;
  }

  await apiFetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ first_name, last_name, username, email, password, confirm_password }),
  });

  flow.registerEmail = email;
  document.getElementById("registerOtpMessage").textContent =
    `We've sent a 6-digit code to ${email}.`;
  showAuthStep("registerOtpStep");
  registerOtp = buildOtpBoxes("registerOtpBoxes");
  startResendCooldown(
    document.getElementById("registerResendLink"),
    document.getElementById("registerResendTimer"),
    () => apiFetch("/auth/register/resend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: flow.registerEmail }),
    })
  );
}

async function verifyRegisterOtp() {
  const code = registerOtp.getCode();
  if (code.length !== OTP_LENGTH) {
    toast("Enter the full 6-digit code.", "error");
    return;
  }
  await apiFetch("/auth/register/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: flow.registerEmail, code }),
  });
  toast("Account verified — please sign in.", "success");
  showLogin();
  document.getElementById("loginEmail").value = flow.registerEmail;
}

// ---------------------------------------------------------------------
// Auth: login
// ---------------------------------------------------------------------
async function login(email, password) {
  const tokens = await apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  session.accessToken = tokens.access_token;
  session.refreshToken = tokens.refresh_token;
  session.user = await apiFetch("/auth/me");
  toast(`Welcome back, ${session.user.full_name || session.user.email}!`, "success");
  renderAuthState();
  loadHistory();
}

function logout() {
  session.accessToken = null;
  session.refreshToken = null;
  session.user = null;
  renderAuthState();
  toast("Signed out.", "info");
}

function renderAuthState() {
  const loggedIn = !!session.user;
  document.getElementById("authPanel").classList.toggle("hidden", loggedIn);
  document.getElementById("appPanel").classList.toggle("hidden", !loggedIn);
  document.getElementById("adminPanel").classList.add("hidden");
  document.getElementById("logoutBtn").classList.toggle("hidden", !loggedIn);

  const isAdmin = loggedIn && session.user.role === "admin";
  document.getElementById("adminNavBtn").classList.toggle("hidden", !isAdmin);

  if (loggedIn) {
    document.getElementById("userLabel").textContent = session.user.full_name || session.user.email;
  } else {
    document.getElementById("userLabel").textContent = "";
    showLogin();
  }
}

// ---------------------------------------------------------------------
// Auth: forgot password (Feature 3 — Email OTP)
// ---------------------------------------------------------------------
function showForgotEmailStep() {
  showAuthStep("forgotEmailStep");
}

async function submitForgotEmail() {
  const email = document.getElementById("forgotEmail").value.trim();
  if (!email) { toast("Enter your account email.", "error"); return; }

  await apiFetch("/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

  flow.forgotEmail = email;
  showAuthStep("forgotOtpStep");
  forgotOtp = buildOtpBoxes("forgotOtpBoxes");
  toast("If that account exists, a code has been sent.", "info");
  startResendCooldown(
    document.getElementById("forgotResendLink"),
    document.getElementById("forgotResendTimer"),
    () => apiFetch("/auth/forgot-password/resend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: flow.forgotEmail }),
    })
  );
}

async function submitForgotOtp() {
  const code = forgotOtp.getCode();
  if (code.length !== OTP_LENGTH) {
    toast("Enter the full 6-digit code.", "error");
    return;
  }
  const result = await apiFetch("/auth/forgot-password/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: flow.forgotEmail, code }),
  });
  flow.resetToken = result.reset_token;
  showAuthStep("forgotNewPasswordStep");
}

async function submitNewPassword() {
  const new_password = document.getElementById("forgotNewPassword").value;
  const confirm_password = document.getElementById("forgotConfirmPassword").value;

  if (!isPasswordValid(new_password)) {
    toast("Password does not meet all requirements.", "error");
    return;
  }
  if (new_password !== confirm_password) {
    toast("Passwords do not match.", "error");
    return;
  }

  await apiFetch("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reset_token: flow.resetToken, new_password, confirm_password }),
  });

  toast("Password updated — please sign in.", "success");
  showLogin();
  document.getElementById("loginEmail").value = flow.forgotEmail;
}

// ---------------------------------------------------------------------
// Admin panel (Feature 7 — RBAC user management)
// ---------------------------------------------------------------------
async function loadAdminUsers() {
  const users = await apiFetch("/admin/users");
  const tbody = document.querySelector("#adminUsersTable tbody");
  tbody.innerHTML = "";
  users.forEach((u) => {
    const tr = document.createElement("tr");
    const isSelf = u.id === session.user.id;
    tr.innerHTML = `
      <td>${u.full_name}</td>
      <td>${u.username}</td>
      <td>${u.email}</td>
      <td><span class="role-badge ${u.role}">${u.role}</span></td>
      <td><span class="status-badge ${u.is_active ? 'active' : 'suspended'}">${u.is_active ? 'Active' : 'Suspended'}</span></td>
      <td class="row-actions">
        ${u.is_active
          ? `<button class="btn secondary" data-action="suspend" data-id="${u.id}" ${isSelf ? "disabled" : ""}>Suspend</button>`
          : `<button class="btn secondary" data-action="activate" data-id="${u.id}">Reactivate</button>`}
        <button class="btn secondary" data-action="delete" data-id="${u.id}" ${isSelf ? "disabled" : ""}>Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll("button[data-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const { action, id } = btn.dataset;
      try {
        if (action === "suspend") await apiFetch(`/admin/users/${id}/suspend`, { method: "POST" });
        if (action === "activate") await apiFetch(`/admin/users/${id}/activate`, { method: "POST" });
        if (action === "delete") {
          if (!confirm("Permanently delete this user?")) return;
          await apiFetch(`/admin/users/${id}`, { method: "DELETE" });
        }
        toast("Done.", "success");
        loadAdminUsers();
      } catch (err) {
        toast(err.message, "error");
      }
    });
  });
}

function showAdminPanel() {
  document.getElementById("appPanel").classList.add("hidden");
  document.getElementById("adminPanel").classList.remove("hidden");
  loadAdminUsers().catch((err) => toast(err.message, "error"));
}

// ---------------------------------------------------------------------
// File pickers (drag & drop)
// ---------------------------------------------------------------------
const pickedFiles = { base: [], compare: [] };

function setupDropzone(zoneId, inputId, kind) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);

  zone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => addFiles(kind, Array.from(input.files)));

  ["dragenter", "dragover"].forEach((evt) =>
    zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.add("dragover"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.remove("dragover"); })
  );
  zone.addEventListener("drop", (e) => addFiles(kind, Array.from(e.dataTransfer.files)));
}

function addFiles(kind, files) {
  pickedFiles[kind].push(...files);
  renderChips(kind);
}

function removeFile(kind, index) {
  pickedFiles[kind].splice(index, 1);
  renderChips(kind);
}

function renderChips(kind) {
  const list = document.getElementById(`${kind}Chips`);
  list.innerHTML = "";
  pickedFiles[kind].forEach((f, i) => {
    const chip = document.createElement("div");
    chip.className = "file-chip";
    chip.innerHTML = `<span>${f.name}</span>`;
    const btn = document.createElement("button");
    btn.textContent = "✕";
    btn.onclick = () => removeFile(kind, i);
    chip.appendChild(btn);
    list.appendChild(chip);
  });
}

// ---------------------------------------------------------------------
// Comparison
// ---------------------------------------------------------------------
async function runComparison() {
  if (pickedFiles.base.length === 0 || pickedFiles.compare.length === 0) {
    toast("Add at least one BASE file and one COMPARE file.", "error");
    return;
  }

  const form = new FormData();
  pickedFiles.base.forEach((f) => form.append("base_files", f));
  pickedFiles.compare.forEach((f) => form.append("compare_files", f));

  const progress = document.getElementById("progressBar");
  const fill = progress.querySelector(".fill");
  progress.style.display = "block";
  fill.style.width = "30%";

  const runBtn = document.getElementById("runBtn");
  runBtn.disabled = true;

  try {
    fill.style.width = "70%";
    const job = await apiFetch("/compare", { method: "POST", body: form });
    fill.style.width = "100%";
    renderResults(job);
    toast("Comparison complete.", "success");
    loadHistory();
  } catch (err) {
    toast(err.message, "error");
  } finally {
    runBtn.disabled = false;
    setTimeout(() => { progress.style.display = "none"; fill.style.width = "0%"; }, 500);
  }
}

function renderResults(job) {
  const tbody = document.querySelector("#resultTable tbody");
  tbody.innerHTML = "";
  (job.results || []).forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.file_name}</td>
      <td>${r.score.toFixed(2)}</td>
      <td><span class="badge ${r.status}">${r.status}</span></td>
    `;
    tbody.appendChild(tr);
  });
  document.getElementById("resultsCard").classList.remove("hidden");
}

// ---------------------------------------------------------------------
// History
// ---------------------------------------------------------------------
async function loadHistory() {
  try {
    const jobs = await apiFetch("/compare/history?limit=10");
    const tbody = document.querySelector("#historyTable tbody");
    tbody.innerHTML = "";
    jobs.forEach((j) => {
      const tr = document.createElement("tr");
      const date = new Date(j.created_at).toLocaleString();
      tr.innerHTML = `
        <td>${date}</td>
        <td>${j.base_file_count}</td>
        <td>${j.compare_file_count}</td>
        <td><span class="badge ${j.status === 'completed' ? 'EXACT' : 'ERROR'}">${j.status}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    // history is best-effort; don't spam toasts on load
    console.warn(err);
  }
}

// ---------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  initTheme();
  renderAuthState();
  setupDropzone("baseDropzone", "baseInput", "base");
  setupDropzone("compareDropzone", "compareInput", "compare");

  document.getElementById("themeToggle").addEventListener("click", toggleTheme);
  document.getElementById("tabLogin").addEventListener("click", showLogin);
  document.getElementById("tabRegister").addEventListener("click", showRegister);
  document.getElementById("logoutBtn").addEventListener("click", () => { logout(); showLogin(); });
  document.getElementById("adminNavBtn").addEventListener("click", showAdminPanel);
  document.getElementById("runBtn").addEventListener("click", runComparison);

  // Password visibility toggles
  document.querySelectorAll(".pw-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = document.getElementById(btn.dataset.target);
      target.type = target.type === "password" ? "text" : "password";
    });
  });

  // Live password strength for register + reset password
  document.getElementById("registerPassword").addEventListener("input", (e) => {
    updatePasswordUI(
      e.target.value,
      document.getElementById("registerStrengthFill"),
      document.getElementById("registerChecklist")
    );
  });
  document.getElementById("forgotNewPassword").addEventListener("input", (e) => {
    updatePasswordUI(
      e.target.value,
      document.getElementById("forgotStrengthFill"),
      document.getElementById("forgotChecklist")
    );
  });

  document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    try { await login(email, password); } catch (err) { toast(err.message, "error"); }
  });

  document.getElementById("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try { await requestRegisterOtp(); } catch (err) { toast(err.message, "error"); }
  });

  document.getElementById("registerOtpSubmit").addEventListener("click", async () => {
    try { await verifyRegisterOtp(); } catch (err) { toast(err.message, "error"); }
  });
  document.getElementById("registerOtpBack").addEventListener("click", showRegister);

  document.getElementById("forgotPasswordLink").addEventListener("click", (e) => {
    e.preventDefault();
    showForgotEmailStep();
  });
  document.getElementById("forgotEmailBack").addEventListener("click", showLogin);
  document.getElementById("forgotEmailSubmit").addEventListener("click", async () => {
    try { await submitForgotEmail(); } catch (err) { toast(err.message, "error"); }
  });
  document.getElementById("forgotOtpSubmit").addEventListener("click", async () => {
    try { await submitForgotOtp(); } catch (err) { toast(err.message, "error"); }
  });
  document.getElementById("forgotResetSubmit").addEventListener("click", async () => {
    try { await submitNewPassword(); } catch (err) { toast(err.message, "error"); }
  });
});
