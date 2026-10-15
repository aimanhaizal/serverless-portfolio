const menuToggle = document.querySelector("#menu-toggle");
const siteNav = document.querySelector("#site-nav");

if (menuToggle && siteNav) {
  menuToggle.addEventListener("click", () => {
    const isOpen = siteNav.classList.toggle("open");
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    menuToggle.setAttribute(
      "aria-label",
      isOpen ? "Close navigation" : "Open navigation"
    );
  });

  siteNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      siteNav.classList.remove("open");
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.setAttribute("aria-label", "Open navigation");
    });
  });
}

const yearElement = document.querySelector("#year");
if (yearElement) {
  yearElement.textContent = new Date().getFullYear();
}

async function loadRepositories() {
  const grid = document.querySelector("#repo-grid");
  const status = document.querySelector("#repo-status");

  if (!grid || !status) return;

  const username = "aimanhaizal";
  const featuredRepo = "serverless-portfolio";

  try {
    const response = await fetch(
      `https://api.github.com/users/${username}/repos?type=owner&sort=updated&direction=desc&per_page=100`,
      {
        headers: { Accept: "application/vnd.github+json" },
      }
    );

    if (!response.ok) {
      if (response.status === 403 || response.status === 429) {
        throw new Error("GitHub API rate limit reached. Please try again later.");
      }
      throw new Error(`GitHub returned HTTP ${response.status}.`);
    }

    const repositories = await response.json();

    const visibleRepositories = repositories
      .filter((repo) => !repo.fork && repo.name !== featuredRepo)
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

    if (visibleRepositories.length === 0) {
      status.textContent = "No other public repositories to display yet.";
      return;
    }

    const fragment = document.createDocumentFragment();

    visibleRepositories.forEach((repo) => {
      const card = document.createElement("article");
      card.className = "project-card repo-card";

      const top = document.createElement("div");
      top.className = "project-top";

      const type = document.createElement("span");
      type.className = "project-type";
      type.textContent = "PUBLIC REPOSITORY";

      const stars = document.createElement("span");
      stars.className = "project-number";
      stars.textContent = `★ ${repo.stargazers_count}`;

      top.append(type, stars);

      const icon = document.createElement("div");
      icon.className = "project-icon";
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = "</>";

      const title = document.createElement("h3");
      title.textContent = repo.name;

      const description = document.createElement("p");
      description.className = "repo-description";
      description.textContent = repo.description || "No description provided yet.";

      const tags = document.createElement("div");
      tags.className = "tags";
      
      if (repo.language) {
        const language = document.createElement("span");
        language.className = "language-tag";
        language.textContent = repo.language;
        tags.append(language);
      }
      
      (repo.topics || []).slice(0, 4).forEach((topic) => {
        const tag = document.createElement("span");
        tag.className = "topic-tag";
        tag.textContent = topic;
        tags.append(tag);
      });
      
      const updated = document.createElement("span");
      updated.textContent =
        `Updated ${new Date(repo.updated_at).toLocaleDateString()}`;
      tags.append(updated);

      const link = document.createElement("a");
      link.className = "text-link";
      link.href = repo.html_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "View repository ↗";

      card.append(top, icon, title, description, tags, link);
      fragment.append(card);
    });

    grid.replaceChildren(fragment);
    status.textContent =
      `Showing ${visibleRepositories.length} other public repositories, fetched live from GitHub and sorted by recent updates.`;
  } catch (error) {
    console.error("Unable to load GitHub repositories:", error);
    status.textContent =
      `${error.message} You can still browse all repositories on GitHub.`;
  }
}

loadRepositories();


function updateAwsStatus(state, message) {
  const buttonLabel = document.querySelector("#aws-status-button-label");
  const title = document.querySelector("#aws-status-title");
  const note = document.querySelector("#aws-status-note");
  const counterLabel = document.querySelector(".aws-counter-label");
  const statusDot = counterLabel?.querySelector(".status-dot");

  const states = {
    checking: {
      label: "Checking AWS...",
      title: "Checking AWS connection",
      counter: "CHECKING BACKEND",
    },
    connected: {
      label: "AWS connected",
      title: "AWS API is responding",
      counter: "LIVE BACKEND RESPONSE",
    },
    unavailable: {
      label: "AWS unavailable",
      title: "AWS API is unavailable",
      counter: "BACKEND UNAVAILABLE",
    },
  };

  const current = states[state];
  if (!current) return;

  if (buttonLabel) buttonLabel.textContent = current.label;
  if (title) title.textContent = current.title;
  if (note) note.textContent = message;
  if (counterLabel) counterLabel.lastChild.textContent = ` ${current.counter}`;

  if (statusDot) {
    statusDot.style.backgroundColor =
      state === "connected" ? "var(--green)" :
      state === "unavailable" ? "#ef4444" :
      "var(--muted)";
    statusDot.style.boxShadow = "none";
  }
}

async function loadVisitorCount() {
  const counter = document.querySelector("#visitor-count");
  if (!counter) return;

  const apiUrl =
    window.PORTFOLIO_CONFIG.apiBaseUrl;

  updateAwsStatus("checking", "Checking the live AWS API.");

  try {
    const response = await fetch(`${apiUrl}/visitors`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) {
      throw new Error(`API returned HTTP ${response.status}`);
    }

    const data = await response.json();

    if (
      typeof data.visitors !== "number" ||
      !Number.isFinite(data.visitors) ||
      data.visitors < 0
    ) {
      throw new Error("Unexpected visitor count response");
    }

    counter.textContent = data.visitors.toLocaleString();
    updateAwsStatus(
      "connected",
      "Live count received from the AWS API."
    );
  } catch (error) {
    console.warn("AWS API unavailable; loading saved snapshot.", error);

    try {
      const response = await fetch("./visitor-count.json", {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Snapshot returned HTTP ${response.status}`);
      }

      const snapshot = await response.json();

      if (
        typeof snapshot.visitors !== "number" ||
        !Number.isFinite(snapshot.visitors) ||
        snapshot.visitors < 0
      ) {
        throw new Error("Invalid visitor snapshot");
      }

      counter.textContent = snapshot.visitors.toLocaleString();

      const isPlaceholder = snapshot.source === "initial-placeholder";
      const timestamp = snapshot.updatedAt
        ? ` Last updated: ${snapshot.updatedAt}.`
        : "";

      updateAwsStatus(
        "unavailable",
        isPlaceholder
          ? "AWS is unavailable. This is an initial placeholder, not a verified historical count."
          : `AWS is unavailable. Showing the last recorded count.${timestamp}`
      );

      const caption = document.querySelector(".aws-counter-caption");
      if (caption) {
        caption.textContent = isPlaceholder
          ? "Initial placeholder · Not a recorded count"
          : "Last recorded visitor counter hits";
      }
    } catch (snapshotError) {
      console.error("Unable to load visitor snapshot:", snapshotError);
      counter.textContent = "Unavailable";
      updateAwsStatus(
        "unavailable",
        "AWS is unavailable and no valid snapshot could be loaded."
      );
    }
  }
}

loadVisitorCount();

function setupAwsStatusToggle() {
  const button = document.querySelector("#aws-status-toggle");
  const details = document.querySelector("#aws-status-details");
  const chevron = document.querySelector("#aws-status-chevron");

  if (!button || !details || !chevron) return;

  button.addEventListener("click", () => {
    const isExpanded = button.getAttribute("aria-expanded") === "true";
    const nextExpanded = !isExpanded;

    button.setAttribute("aria-expanded", String(nextExpanded));
    details.hidden = !nextExpanded;
    chevron.textContent = nextExpanded ? "−" : "+";
  });
}

setupAwsStatusToggle();




async function setupPixelEditor() {
  const canvas = document.querySelector("#pixel-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const palette = document.querySelector("#pixel-palette");
  const clearButton = document.querySelector("#pixel-clear");
  const saveButton = document.querySelector("#pixel-save");
  const status = document.querySelector("#pixel-status");

  if (!ctx || !palette || !clearButton || !saveButton || !status) return;

  const apiUrl = window.PORTFOLIO_CONFIG.apiBaseUrl;
  const endpoint = `${apiUrl}/canvas`;
  const size = 16;
  const cell = canvas.width / size;
  const colors = ["#ffffff", "#111718", "#ff4b4b", "#367bf5"];

  let pixels = Array(size * size).fill(0);
  let selectedColor = 2;
  let drawing = false;
  let lastCell = -1;
  let saving = false;
  let dirty = false;

  function render() {
    pixels.forEach((colorIndex, index) => {
      ctx.fillStyle = colors[colorIndex];
      ctx.fillRect(
        (index % size) * cell,
        Math.floor(index / size) * cell,
        cell,
        cell
      );
    });

    ctx.strokeStyle = "rgba(11, 15, 16, 0.16)";
    ctx.lineWidth = 1;

    for (let i = 0; i <= size; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cell, 0);
      ctx.lineTo(i * cell, canvas.height);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(0, i * cell);
      ctx.lineTo(canvas.width, i * cell);
      ctx.stroke();
    }
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function setDirty(message = "Unsaved local draft.") {
    dirty = true;
    setStatus(message);
  }

  function paint(event) {
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor(((event.clientX - rect.left) / rect.width) * size);
    const y = Math.floor(((event.clientY - rect.top) / rect.height) * size);

    if (x < 0 || x >= size || y < 0 || y >= size) return;

    const index = y * size + x;
    if (index === lastCell) return;

    lastCell = index;

    if (pixels[index] === selectedColor) return;

    pixels[index] = selectedColor;
    render();
    setDirty();
  }

  async function loadCanvas() {
    setStatus("Loading shared canvas from AWS...");

    try {
      const response = await fetch(endpoint, {
        cache: "no-store",
        signal: AbortSignal.timeout(8000),
      });

      if (!response.ok) {
        throw new Error(`API returned HTTP ${response.status}`);
      }

      const data = await response.json();

      if (
        !Array.isArray(data.pixels) ||
        data.pixels.length !== size * size ||
        !data.pixels.every(
          (pixel) => Number.isInteger(pixel) && pixel >= 0 && pixel < colors.length
        )
      ) {
        throw new Error("The API returned invalid canvas data.");
      }

      pixels = data.pixels.slice();
      dirty = false;
      render();

      const savedAt = data.updatedAt
        ? new Date(data.updatedAt).toLocaleString()
        : null;

      setStatus(
        savedAt
          ? `Shared canvas loaded. Last saved: ${savedAt}.`
          : "Shared canvas loaded. No saved artwork yet."
      );
    } catch (error) {
      console.error("Unable to load shared canvas:", error);
      setStatus("Couldn't load the shared canvas. You can still draw, then try Save.");
    }
  }

  canvas.addEventListener("pointerdown", (event) => {
    if (saving || (event.button !== 0 && event.pointerType === "mouse")) return;

    event.preventDefault();
    drawing = true;
    lastCell = -1;
    canvas.setPointerCapture(event.pointerId);
    paint(event);
  });

  canvas.addEventListener("pointermove", (event) => {
    if (drawing && !saving) paint(event);
  });

  function stopDrawing() {
    drawing = false;
    lastCell = -1;
  }

  canvas.addEventListener("pointerup", stopDrawing);
  canvas.addEventListener("pointercancel", stopDrawing);
  canvas.addEventListener("lostpointercapture", stopDrawing);

  palette.addEventListener("click", (event) => {
    const button = event.target.closest(".palette-swatch");
    if (!button || saving) return;

    const color = Number(button.dataset.color);
    if (!Number.isInteger(color) || color < 0 || color >= colors.length) return;

    selectedColor = color;

    palette.querySelectorAll(".palette-swatch").forEach((swatch) => {
      const selected = swatch === button;
      swatch.classList.toggle("is-selected", selected);
      swatch.setAttribute("aria-pressed", String(selected));
    });
  });

  clearButton.addEventListener("click", () => {
    if (saving) return;

    pixels = Array(size * size).fill(0);
    render();
    setDirty("Cleared locally. Save to clear the shared canvas.");
  });

  saveButton.addEventListener("click", async () => {
    if (saving) return;

    saving = true;
    saveButton.disabled = true;
    clearButton.disabled = true;
    setStatus("Saving shared canvas to AWS...");

    try {
      const response = await fetch(endpoint, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pixels: pixels.slice() }),
        signal: AbortSignal.timeout(10000),
      });

      if (!response.ok) {
        throw new Error(`API returned HTTP ${response.status}`);
      }

      const data = await response.json();

      if (
        !Array.isArray(data.pixels) ||
        data.pixels.length !== size * size ||
        !data.pixels.every(
          (pixel) => Number.isInteger(pixel) && pixel >= 0 && pixel < colors.length
        )
      ) {
        throw new Error("The API returned an invalid save response.");
      }

      pixels = data.pixels.slice();
      dirty = false;
      render();

      const savedAt = data.updatedAt
        ? new Date(data.updatedAt).toLocaleString()
        : "just now";

      setStatus(`Saved to the shared canvas at ${savedAt}.`);
    } catch (error) {
      console.error("Unable to save shared canvas:", error);
      setStatus(
        "Couldn't save to AWS. Your draft is still on this page; please try again."
      );
    } finally {
      saving = false;
      saveButton.disabled = false;
      clearButton.disabled = false;
    }
  });

  window.addEventListener("beforeunload", (event) => {
    if (!dirty) return;
    event.preventDefault();
    event.returnValue = "";
  });

  render();
  await loadCanvas();
}

setupPixelEditor();

