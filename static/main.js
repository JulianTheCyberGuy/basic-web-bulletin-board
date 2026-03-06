let lastTimestamp = "";
let currentUser = null;

function formatTimestamp(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: "America/New_York",
    timeZoneName: "short"
  });
}

function renderPost(p) {
  const div = document.createElement("div");
  div.className = "post";

  const timestamp = document.createElement("div");
  timestamp.className = "timestamp";
  timestamp.textContent = formatTimestamp(p.created_at);

  const author = document.createElement("div");
  author.className = "author";
  author.textContent = p.author_email;

  const body = document.createElement("div");
  body.className = "post-body";
  body.textContent = p.body;

  div.appendChild(timestamp);
  div.appendChild(author);
  div.appendChild(body);

  return div;
}

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.style.display = "block";
}

function clearError(id) {
  const el = document.getElementById(id);
  el.textContent = "";
  el.style.display = "none";
}

function updateAuthUi() {
  const authStatus = document.getElementById("authStatus");
  const postHint = document.getElementById("postHint");
  const postButton = document.querySelector("#postForm button[type='submit']");

  if (currentUser) {
    authStatus.textContent = `Logged in as ${currentUser.email}`;
    postHint.textContent = `Your post will publish as ${currentUser.email}.`;
    postButton.disabled = false;
  } else {
    authStatus.textContent = "Not logged in.";
    postHint.textContent = "Log in to publish a post.";
    postButton.disabled = true;
  }
}

async function loadCurrentUser() {
  try {
    const res = await fetch("/api/me", { credentials: "same-origin" });
    if (!res.ok) {
      currentUser = null;
      updateAuthUi();
      return;
    }

    currentUser = await res.json();
    updateAuthUi();
  } catch {
    currentUser = null;
    updateAuthUi();
  }
}

async function loadAllPosts() {
  const res = await fetch("/api/posts");
  const posts = await res.json();

  const container = document.getElementById("posts");
  container.innerHTML = "";

  for (const p of posts) {
    container.appendChild(renderPost(p));
    lastTimestamp = p.created_at;
  }
}

async function fetchNewPosts() {
  const url = lastTimestamp
    ? `/api/posts?since=${encodeURIComponent(lastTimestamp)}`
    : "/api/posts";

  const res = await fetch(url);
  const newPosts = await res.json();
  if (!Array.isArray(newPosts) || newPosts.length === 0) return;

  const container = document.getElementById("posts");
  for (const p of newPosts) {
    container.appendChild(renderPost(p));
    lastTimestamp = p.created_at;
  }
}

async function register(email, password) {
  const res = await fetch("/api/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to register.");
  return data;
}

async function login(email, password) {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to login.");
  return data;
}

async function logout() {
  await fetch("/api/logout", {
    method: "POST",
    credentials: "same-origin"
  });
}

async function submitPost(body) {
  const res = await fetch("/api/posts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ body })
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to post.");
  return data;
}

document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError("authError");

  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value;

  try {
    await register(email, password);
    document.getElementById("registerPassword").value = "";
    showError("authError", "Registration successful. You can log in now.");
  } catch (err) {
    showError("authError", err.message);
  }
});

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError("authError");

  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  try {
    await login(email, password);
    document.getElementById("loginPassword").value = "";
    await loadCurrentUser();
  } catch (err) {
    showError("authError", err.message);
  }
});

document.getElementById("logoutButton").addEventListener("click", async () => {
  clearError("authError");
  await logout();
  currentUser = null;
  updateAuthUi();
});

document.getElementById("postForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError("formError");

  const body = document.getElementById("body").value.trim();

  try {
    await submitPost(body);
    document.getElementById("body").value = "";
    await fetchNewPosts();
  } catch (err) {
    showError("formError", err.message);
  }
});

loadCurrentUser();
loadAllPosts();
setInterval(fetchNewPosts, 5000);
