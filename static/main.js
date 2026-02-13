let lastTimestamp = "";

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[c]));
}

function renderPost(p) {
  const div = document.createElement("div");
  div.className = "post";

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = `${p.created_at} | ${p.author_email}`;

  const body = document.createElement("div");
  body.innerHTML = escapeHtml(p.body).replace(/\n/g, "<br>");

  div.appendChild(meta);
  div.appendChild(body);
  return div;
}

function showError(msg) {
  const el = document.getElementById("formError");
  el.textContent = msg;
  el.style.display = "block";
}

function clearError() {
  const el = document.getElementById("formError");
  el.textContent = "";
  el.style.display = "none";
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

async function submitPost(email, body) {
  const res = await fetch("/api/posts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ author_email: email, body })
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to post.");
  return data;
}

document.getElementById("postForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();

  const email = document.getElementById("email").value.trim();
  const body = document.getElementById("body").value.trim();

  try {
    await submitPost(email, body);
    document.getElementById("body").value = "";
    await fetchNewPosts();
  } catch (err) {
    showError(err.message);
  }
});

loadAllPosts();
setInterval(fetchNewPosts, 5000);
