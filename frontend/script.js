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


async function loadVisitorCount() {
  const counter = document.querySelector("#visitor-count");
  if (!counter) return;

  const apiUrl =
    "https://vwrhwdy26e.execute-api.ap-southeast-1.amazonaws.com";

  try {
    const response = await fetch(`${apiUrl}/visitors`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`API returned HTTP ${response.status}`);
    }

    const data = await response.json();

    if (typeof data.visitors !== "number") {
      throw new Error("Unexpected visitor count response");
    }

    counter.textContent = data.visitors.toLocaleString();
  } catch (error) {
    console.error("Unable to load visitor count:", error);
    counter.textContent = "Currently unavailable";
  }
}

loadVisitorCount();
