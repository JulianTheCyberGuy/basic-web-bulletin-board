const MAX_POST_LENGTH = 2000;

let lastTimestamp = "";
let currentUser = null;
let postCount = 0;

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

function initialsFromEmail(email) {
  const base = (email || "?").split("@")[0].replace(/[^a-zA-Z0-9]/g, "");
  return (base.slice(0, 2) || "?").toUpperCase();
}

function setMessage(id, type, msg) {
  const el = document.getElementById(id);
  el.className = `message ${type}`;
  el.textContent = msg;
  el.style.display = msg ? "block" : "none";
}

function clearMessage(id) {
  const el = document.getElementById(id);
  el.className = "message";
  el.textContent = "";
  el.style.display = "none";
}

function updateCharCount() {
  const body = document.getElementById("body").value || "";
  const charCount = document.getElementById("charCount");
  charCount.textContent = `${body.length} / ${MAX_POST_LENGTH}`;
}

function updateFeedCount() {
  const countLabel = postCount === 1 ? "post" : "posts";
  document.getElementById("feedCount").textContent = `${postCount} ${countLabel}`;
}

function renderEmptyState() {
  const container = document.getElementById("posts");
  container.innerHTML = `
    <div class="empty-state">
      <strong>No posts yet</strong>
      The feed is empty right now. Be the first person to share an update.
    </div>
  `;
  postCount = 0;
  updateFeedCount();
}

function buildPostElement(p) {
  const article = document.createElement("article");
  article.className = "post";

  article.innerHTML = `
    <div class="post-head">
      <div class="post-author">
        <div class="avatar">${initialsFromEmail(p.author_email)}</div>
        <div>
          <p class="author-name">${p.author_email}</p>
          <p class="author-tag">Community member</p>
        </div>
      </div>
      <div class="timestamp">${formatTimestamp(p.created_at)}</div>
    </div>
    <div class="post-body"></div>
  `;

  article.querySelector(".post-body").textContent = p.body;
  return article;
}

function renderAllPosts(posts) {
  const container = document.getElementById("posts");
  container.innerHTML = "";

  if (!Array.isArray(posts) || posts.length === 0) {
    renderEmptyState();
    lastTimestamp = "";
    return;
  }

  for (const p of posts) {
    container.appendChild(buildPostElement(p));
  }

  lastTimestamp = posts[posts.length - 1].created_at;
  postCount = posts.length;
  updateFeedCount();
}

function appendPosts(posts) {
  if (!Array.isArray(posts) || posts.length === 0) return;

  const container = document.getElementById("posts");
  const emptyState = container.querySelector(".empty-state");
  if (emptyState) {
    container.innerHTML = "";
  }

  for (const p of posts) {
    container.appendChild(buildPostElement(p));
    lastTimestamp = p.created_at;
    postCount += 1;
  }

  updateFeedCount();
}

function updateAuthUi() {
  const authStatusPill = document.getElementById("authStatusPill");
  const postHint = document.getElementById("postHint");
  const postButton = document.querySelector("#postForm button[type='submit']");
  const logoutButton = document.getElementById("logoutButton");
  const composerPanel = document.getElementById("composerPanel");
  const bodyInput = document.getElementById("body");

  if (currentUser) {
    authStatusPill.textContent = "Logged in";
    authStatusPill.className = "status-pill success";
    postHint.textContent = `Your post will publish as ${currentUser.email}.`;
    postButton.disabled = false;
    logoutButton.style.display = "inline-flex";
    bodyInput.disabled = false;
    composerPanel.classList.remove("composer-disabled");
  } else {
    authStatusPill.textContent = "Not logged in";
    authStatusPill.className = "status-pill neutral";
    postHint.textContent = "Log in to publish a post.";
    postButton.disabled = true;
    logoutButton.style.display = "none";
    bodyInput.disabled = true;
    composerPanel.classList.add("composer-disabled");
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
  try {
    const res = await fetch("/api/posts");
    const posts = await res.json();
    renderAllPosts(posts);
  } catch {
    renderEmptyState();
  }
}

async function fetchNewPosts() {
  try {
    const url = lastTimestamp
      ? `/api/posts?since=${encodeURIComponent(lastTimestamp)}`
      : "/api/posts";

    const res = await fetch(url);
    const newPosts = await res.json();
    appendPosts(newPosts);
  } catch {
    // Keep UI stable if polling fails.
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
  clearMessage("authMessage");

  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value;

  try {
    await register(email, password);
    document.getElementById("registerPassword").value = "";
    setMessage("authMessage", "success", "Registration successful. You can log in now.");
  } catch (err) {
    setMessage("authMessage", "error", err.message);
  }
});

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearMessage("authMessage");

  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  try {
    await login(email, password);
    document.getElementById("loginPassword").value = "";
    await loadCurrentUser();
    setMessage("authMessage", "success", `Welcome back, ${email}.`);
  } catch (err) {
    setMessage("authMessage", "error", err.message);
  }
});

document.getElementById("logoutButton").addEventListener("click", async () => {
  clearMessage("authMessage");
  await logout();
  currentUser = null;
  updateAuthUi();
  setMessage("authMessage", "success", "You have been logged out.");
});

document.getElementById("postForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearMessage("formMessage");

  const body = document.getElementById("body").value.trim();

  try {
    await submitPost(body);
    document.getElementById("body").value = "";
    updateCharCount();
    await fetchNewPosts();
    setMessage("formMessage", "success", "Your post is now live.");
  } catch (err) {
    setMessage("formMessage", "error", err.message);
  }
});

document.getElementById("refreshButton").addEventListener("click", async () => {
  await loadAllPosts();
});

document.getElementById("body").addEventListener("input", updateCharCount);

updateCharCount();
loadCurrentUser();
loadAllPosts();
setInterval(fetchNewPosts, 5000);
