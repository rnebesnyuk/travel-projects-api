async function api(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const contentType = resp.headers.get("content-type") || "";
  let data = null;
  if (contentType.includes("application/json")) {
    data = await resp.json().catch(() => null);
  } else {
    data = await resp.text().catch(() => null);
  }

  if (!resp.ok) {
    const detail = data && data.detail ? data.detail : JSON.stringify(data);
    throw new Error(`${resp.status} ${resp.statusText}\n${detail}`);
  }
  return data;
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === "class") node.className = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  });
  children.forEach((c) => node.appendChild(typeof c === "string" ? document.createTextNode(c) : c));
  return node;
}

function parsePlaceIds(input) {
  const raw = input.split(",").map(s => s.trim()).filter(Boolean);
  const ids = raw.map(x => Number(x)).filter(n => Number.isInteger(n) && n > 0);
  if (ids.length !== raw.length) {
    throw new Error("Places must be comma-separated positive integers, e.g. 27992,129884");
  }
  return ids;
}

async function loadProjects() {
  const msg = document.getElementById("msg");
  msg.textContent = "Loading...";
  try {
    const projects = await api("/projects");
    msg.textContent = `Loaded ${projects.length} project(s).`;
    renderProjects(projects);
  } catch (e) {
    msg.textContent = "";
    msg.className = "error";
    msg.textContent = e.message;
  }
}

function renderProjects(projects) {
  const container = document.getElementById("projects");
  container.innerHTML = "";

  projects.forEach((p) => {
    const card = el("div", { class: "card" });

    card.appendChild(el("div", {}, [el("strong", {}, [`#${p.id} ${p.name}`])]));
    card.appendChild(el("div", { class: "muted" }, [`status: ${p.status}`]));
    card.appendChild(el("div", { class: "muted" }, [`start_date: ${p.start_date || "-"}`]));

    // Update form
    const nameInput = el("input", { value: p.name });
    const descInput = el("textarea", { rows: "2" }, []);
    descInput.value = ""; // keep optional; you can fetch full project if you want description shown
    const dateInput = el("input", { type: "date", value: p.start_date || "" });

    const btnOpen = el("button", {
      onclick: () => (window.location.href = `/projects/${p.id}/ui`)
    }, ["Open"]);

    const btnUpdate = el("button", {
      onclick: async () => {
        try {
          await api(`/projects/${p.id}`, {
            method: "PATCH",
            body: JSON.stringify({
              name: nameInput.value.trim() || undefined,
              description: descInput.value || undefined,
              start_date: dateInput.value || undefined,
            }),
          });
          await loadProjects();
        } catch (e) {
          alert(e.message);
        }
      }
    }, ["Update"]);

    const btnDelete = el("button", {
      onclick: async () => {
        if (!confirm(`Delete project #${p.id}?`)) return;
        try {
          await api(`/projects/${p.id}`, { method: "DELETE" });
          await loadProjects();
        } catch (e) {
          alert(e.message);
        }
      }
    }, ["Delete"]);

    card.appendChild(el("hr"));
    card.appendChild(el("div", { class: "muted" }, ["Quick edit (optional):"]));
    card.appendChild(el("label", { class: "muted" }, ["Name"]));
    card.appendChild(nameInput);
    card.appendChild(el("label", { class: "muted" }, ["Description (optional)"]));
    card.appendChild(descInput);
    card.appendChild(el("label", { class: "muted" }, ["Start date"]));
    card.appendChild(dateInput);

    card.appendChild(el("div", {}, [btnOpen, btnUpdate, btnDelete]));
    container.appendChild(card);
  });
}

async function createProject() {
  const msg = document.getElementById("create_msg");
  msg.className = "muted";
  msg.textContent = "Creating...";

  try {
    const name = document.getElementById("p_name").value.trim();
    const description = document.getElementById("p_desc").value.trim() || null;
    const start_date = document.getElementById("p_date").value || null;
    const ids = parsePlaceIds(document.getElementById("p_places").value);

    const places = ids.map((id) => ({ external_id: id }));

    await api("/projects", {
      method: "POST",
      body: JSON.stringify({ name, description, start_date, places }),
    });

    msg.className = "ok";
    msg.textContent = "Created!";
    document.getElementById("p_name").value = "";
    document.getElementById("p_desc").value = "";
    document.getElementById("p_date").value = "";
    document.getElementById("p_places").value = "";

    await loadProjects();
  } catch (e) {
    msg.className = "error";
    msg.textContent = e.message;
  }
}

document.getElementById("btn_create").addEventListener("click", createProject);
loadProjects();
