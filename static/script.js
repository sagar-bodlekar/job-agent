/**
 * Job Agent UI - Frontend Interactivity
 */

(function () {
  "use strict";

  // ---- DOM refs ----
  const form = document.getElementById("scrapeForm");
  const jobInput = document.getElementById("jobTitle");
  const platformTiles = document.querySelectorAll(".platform-tile");
  const scrapeBtn = document.getElementById("scrapeBtn");
  const progressBar = document.getElementById("progressBar");
  const resultsBody = document.getElementById("resultsBody");
  const emptyState = document.getElementById("emptyState");
  const resultsTable = document.getElementById("resultsTable");
  const totalJobsEl = document.getElementById("totalJobs");
  const platformsActiveEl = document.getElementById("platformsActive");
  const latestRunEl = document.getElementById("latestRun");
  const downloadBtn = document.getElementById("downloadBtn");
  const toastContainer = document.getElementById("toastContainer");

  // ---- State ----
  let isScraping = false;

  // ---- Platform Tiles ----
  platformTiles.forEach((tile) => {
    tile.addEventListener("click", () => {
      if (isScraping) return;
      tile.classList.toggle("active");
    });
  });

  // ---- Form Submit ----
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (isScraping) return;

    const jobTitle = jobInput.value.trim();
    if (!jobTitle) {
      showToast("Please enter a job title", "error");
      jobInput.focus();
      return;
    }

    const selected = [...platformTiles]
      .filter((t) => t.classList.contains("active"))
      .map((t) => t.dataset.platform);

    if (selected.length === 0) {
      showToast("Please select at least one platform", "error");
      return;
    }

    await startScraping(jobTitle, selected);
  });

  // ---- Scrape Logic ----
  async function startScraping(title, platforms) {
    isScraping = true;
    scrapeBtn.classList.add("loading");
    scrapeBtn.disabled = true;
    progressBar.classList.add("visible");
    progressBar.querySelector(".progress-bar").style.width = "10%";

    showToast(`Scraping "${title}" on ${platforms.join(", ")}...`, "info");

    try {
      const resp = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_title: title, platforms, max_pages: 2 }),
      });

      progressBar.querySelector(".progress-bar").style.width = "80%";

      const data = await resp.json();

      if (!data.success) {
        showToast(data.error || "Scraping failed", "error");
        return;
      }

      progressBar.querySelector(".progress-bar").style.width = "100%";
      setTimeout(() => {
        progressBar.classList.remove("visible");
        progressBar.querySelector(".progress-bar").style.width = "0%";
      }, 600);

      renderResults(data);
      showToast(
        `Found ${data.total} job${data.total !== 1 ? "s" : ""} across ${data.platforms.length} platform${data.platforms.length !== 1 ? "s" : ""}!`,
        "success"
      );
    } catch (err) {
      showToast("Network error: " + err.message, "error");
      progressBar.classList.remove("visible");
    } finally {
      isScraping = false;
      scrapeBtn.classList.remove("loading");
      scrapeBtn.disabled = false;
    }
  }

  // ---- Render Results ----
  function renderResults(data) {
    const { jobs, total, platforms } = data;

    // Update stats
    totalJobsEl.textContent = total;
    platformsActiveEl.textContent = platforms.length;
    latestRunEl.textContent = new Date().toLocaleTimeString();

    // Toggle table / empty state
    if (total === 0) {
      emptyState.style.display = "block";
      resultsTable.style.display = "none";
      downloadBtn.style.display = "none";
      return;
    }

    emptyState.style.display = "none";
    resultsTable.style.display = "table";
    downloadBtn.style.display = "flex";

    // Build rows
    const fragment = document.createDocumentFragment();

    jobs.forEach((job, index) => {
      const tr = document.createElement("tr");
      tr.style.animationDelay = `${index * 0.04}s`;

      const platformClass = job.source_platform.toLowerCase();

      tr.innerHTML = `
        <td>
          <div class="company-name">${escapeHtml(job.title)}</div>
        </td>
        <td>${escapeHtml(job.company)}</td>
        <td><span class="location-text">${escapeHtml(job.location)}</span></td>
        <td>${job.salary ? `<span class="salary-text">${escapeHtml(job.salary)}</span>` : '<span class="text-muted">—</span>'}</td>
        <td>
          <a href="${escapeHtml(job.link)}" target="_blank" rel="noopener" class="job-link">
            View ↗
          </a>
        </td>
        <td>
          <span class="platform-badge ${platformClass}">${job.source_platform}</span>
        </td>
      `;

      fragment.appendChild(tr);
    });

    // Clear and append
    resultsBody.innerHTML = "";
    resultsBody.appendChild(fragment);
  }

  // ---- Download CSV ----
  downloadBtn.addEventListener("click", () => {
    window.location.href = "/download";
  });

  // ---- Toast Notifications ----
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let iconSvg = "";
    if (type === "success") {
      iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
    } else if (type === "error") {
      iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
    } else {
      iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    }

    toast.innerHTML = `${iconSvg}<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("toast-out");
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // ---- Utility ----
  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ---- Load existing data on page load ----
  async function loadExistingJobs() {
    try {
      const resp = await fetch("/api/jobs");
      const data = await resp.json();
      if (data.success && data.jobs.length > 0) {
        renderResults(data);
      }
    } catch (_) {
      // silently ignore — no cached data
    }
  }

  loadExistingJobs();
})();
