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

async function loadProject() {
  document.getElementById("project_id").textContent = `#${window.PROJECT_ID}`;
  const info = document.getElementById("project_info");
  info.textContent = "Loading...";

  try {
    const project = await api(`/projects/${window.PROJECT_ID}`);
    info.innerHTML = "";
    info.appendChild(el("div", {}, [el("strong", {}, [project.name])]));
    info.appendChild(el("div", { class: "muted" }, [`status: ${project.status}`]));
    info.appendChild(el("div", { class: "muted" }, [`start_date: ${project.start_date || "-"}`]));
    info.appendChild(el("div", { class: "muted" }, [`places: ${project.places.length}`]));
  } catch (e) {
    info.className = "card error";
    info.textContent = e.message;
  }
}

async function loadPlaces() {
  const msg = document.getElementById("places_msg");
  const container = document.getElementById("places");
  msg.textContent = "Loading places...";
  container.innerHTML = "";

  try {
    const places = await api(`/projects/${window.PROJECT_ID}/places`);
    msg.textContent = `Loaded ${places.length} place(s).`;

    places.forEach((p) => {
      const card = el("div", { class: "card" });

      card.appendChild(el("div", {}, [
        el("strong", {}, [`Place #${p.id}`]),
        el("span", { class: "pill", style: "margin-left:8px" }, [`external_id: ${p.external_id}`]),
      ]));

      const notes = el("textarea", { rows: "3" }, []);
      notes.value = p.notes || "";

      const visited = el("select", {}, [
        el("option", { value: "false" }, ["not visited"]),
        el("option", { value: "true" }, ["visited"]),
      ]);
      visited.value = String(!!p.visited);

      const btnSave = el("button", {
        onclick: async () => {
          try {
            await api(`/projects/${window.PROJECT_ID}/places/${p.id}`, {
              method: "PATCH",
              body: JSON.stringify({
                notes: notes.value,
                visited: visited.value === "true",
              }),
            });
            await loadProject(); // status might change
            await loadPlaces();
          } catch (e) {
            alert(e.message);
          }
        }
      }, ["Save"]);

      card.appendChild(el("div", { class: "muted" }, ["Notes:"]));
      card.appendChild(notes);

      card.appendChild(el("div", { class: "muted" }, ["Visited:"]));
      card.appendChild(visited);

      card.appendChild(btnSave);
      container.appendChild(card);
    });
  } catch (e) {
    msg.className = "error";
    msg.textContent = e.message;
  }
}

async function addPlace() {
  const msg = document.getElementById("add_msg");
  msg.className = "muted";
  msg.textContent = "Adding...";

  try {
    const external_id = Number(document.getElementById("add_external_id").value.trim());
    if (!Number.isInteger(external_id) || external_id <= 0) {
      throw new Error("External ID must be a positive integer.");
    }
    const notes = document.getElementById("add_notes").value || null;

    await api(`/projects/${window.PROJECT_ID}/places`, {
      method: "POST",
      body: JSON.stringify({ external_id, notes }),
    });

    msg.className = "ok";
    msg.textContent = "Added!";
    document.getElementById("add_external_id").value = "";
    document.getElementById("add_notes").value = "";

    await loadProject();
    await loadPlaces();
  } catch (e) {
    msg.className = "error";
    msg.textContent = e.message;
  }
}

document.getElementById("btn_add").addEventListener("click", addPlace);

loadProject();
loadPlaces();
