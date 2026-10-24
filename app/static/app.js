(() => {
  "use strict";

  // All user-visible text is inserted with textContent, never as markup,
  // so nothing a user or the AI returns can run as script.

  const $ = (id) => document.getElementById(id);
  const form = $("plan-form");
  const submitBtn = $("submit-btn");
  const formError = $("form-error");
  const results = $("results");

  const FIELD_LABELS = {
    event_type: "Type of event",
    title: "Event name",
    event_date: "Event date",
    guest_count: "Number of guests",
    total_budget: "Total budget",
    currency: "Currency",
    location: "City or area",
    preferences: "Wishes and preferences",
  };

  const PLACEHOLDERS = {
    wedding: { title: "Asha & Ravi's wedding", preferences: "e.g. vegetarian food, outdoor, traditional music" },
    birthday: { title: "Mira's 8th birthday", preferences: "e.g. kids attending, superhero theme, eggless cake" },
    community: { title: "Ward 12 Diwali fair", preferences: "e.g. free entry, stalls, eco-friendly, seating for elders" },
  };

  let currentPlan = null;
  let storageKey = "";

  // ------------------------------------------------------------------ helpers

  function h(tag, options = {}, children = []) {
    const node = document.createElement(tag);
    if (options.class) node.className = options.class;
    if (options.text !== undefined) node.textContent = options.text;
    if (options.attrs) {
      for (const [name, value] of Object.entries(options.attrs)) node.setAttribute(name, value);
    }
    for (const child of children) node.append(child);
    return node;
  }

  function moneyFormatter(currency) {
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency, maximumFractionDigits: 0 });
    } catch {
      return { format: (n) => `${currency} ${Math.round(n).toLocaleString()}` };
    }
  }

  function formatDate(iso) {
    const [year, month, day] = iso.split("-").map(Number);
    return new Date(year, month - 1, day).toLocaleDateString(undefined, {
      day: "numeric", month: "short", year: "numeric",
    });
  }

  function isoDate(date) {
    const pad = (n) => String(n).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  }

  function loadChecked() {
    try {
      return JSON.parse(localStorage.getItem(storageKey) || "{}");
    } catch {
      return {};
    }
  }

  function saveChecked(state) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      /* private mode or storage full: progress simply isn't remembered */
    }
  }

  function describeError(status, body) {
    if (status === 429) return "Too many requests. Please wait a minute and try again.";
    if (status === 413) return "That request was too large. Please shorten your text.";
    if (status === 422 && body && Array.isArray(body.detail)) {
      return body.detail
        .map((item) => {
          const field = item.loc && item.loc[item.loc.length - 1];
          return `${FIELD_LABELS[field] || "Input"}: ${item.msg}`;
        })
        .join("\n");
    }
    return "Something went wrong on our side. Please try again in a moment.";
  }

  // ---------------------------------------------------------------- rendering

  function checkRow(id, title, meta, checkedState) {
    const input = h("input", { attrs: { type: "checkbox", "data-id": id } });
    input.checked = Boolean(checkedState[id]);
    const body = h("span", { class: "check-body" }, [
      h("span", { class: "check-title", text: title }),
      h("span", { class: "check-meta", text: meta }),
    ]);
    return h("label", { class: "check" }, [input, body]);
  }

  function renderSummary(plan, money) {
    const { summary, request } = plan;
    $("plan-title").textContent = request.title;
    const items = [
      ["Event date", formatDate(request.event_date)],
      ["Days to go", String(summary.days_until_event)],
      ["Guests", String(request.guest_count)],
      ["Total budget", money.format(request.total_budget)],
      ["Budget per guest", money.format(summary.budget_per_guest)],
    ];
    const list = $("summary");
    list.replaceChildren(
      ...items.map(([term, value]) =>
        h("div", {}, [h("dt", { text: term }), h("dd", { text: value })])
      )
    );
    $("warnings").replaceChildren(...summary.warnings.map((text) => h("li", { text })));
  }

  function renderBudget(plan, money) {
    const rows = plan.budget.map((line) =>
      h("tr", {}, [
        h("th", { attrs: { scope: "row" }, text: line.category }),
        h("td", { class: "num", text: `${line.percent}%` }),
        h("td", { class: "num", text: money.format(line.amount) }),
        h("td", { class: "num", text: money.format(line.per_guest) }),
      ])
    );
    $("budget-table").querySelector("tbody").replaceChildren(...rows);
    const total = plan.budget.reduce((sum, line) => sum + line.amount, 0);
    $("budget-table").querySelector("tfoot").replaceChildren(
      h("tr", {}, [
        h("td", { text: "Total" }),
        h("td", { class: "num", text: "100%" }),
        h("td", { class: "num", text: money.format(total) }),
        h("td", { class: "num", text: money.format(plan.summary.budget_per_guest) }),
      ])
    );
  }

  function renderTimeline(plan, checked) {
    $("timeline").replaceChildren(
      ...plan.timeline.map((item) =>
        h("li", {}, [
          checkRow(
            `timeline-${item.id}`,
            item.title,
            `Do by ${formatDate(item.due_date)} - ${item.category}`,
            checked
          ),
        ])
      )
    );
  }

  function renderVendors(plan, checked) {
    $("vendors").replaceChildren(
      ...plan.vendors.map((vendor, index) => {
        const questions = h("ul", {}, vendor.questions.map((q) => h("li", { text: q })));
        return h("div", { class: "vendor" }, [
          h("h3", { text: vendor.category }),
          h("p", { class: "check-meta" }, [
            h("span", { class: `priority-${vendor.priority}`, text: `${vendor.priority} priority` }),
            document.createTextNode(` - book by ${formatDate(vendor.book_by)}`),
          ]),
          checkRow(`vendor-${index}`, "Booked", "", checked),
          h("p", { class: "check-meta", text: "Questions to ask:" }),
          questions,
        ]);
      })
    );
  }

  function renderIdeas(plan) {
    const sections = [
      ["Themes", plan.ideas.themes],
      ["Activities", plan.ideas.activities],
      ["Menu", plan.ideas.menu],
      ["Tips", plan.ideas.tips],
    ];
    $("ideas").replaceChildren(
      ...sections.map(([title, items]) =>
        h("div", { class: "idea-block" }, [
          h("h3", { text: title }),
          h("ul", {}, items.map((text) => h("li", { text }))),
        ])
      )
    );
    $("ideas-source").textContent = plan.ideas.source === "ai" ? "AI-personalised" : "Built-in suggestions";
  }

  function updateProgress() {
    const boxes = results.querySelectorAll("input[type=checkbox]");
    const done = Array.from(boxes).filter((box) => box.checked).length;
    $("progress").max = Math.max(boxes.length, 1);
    $("progress").value = done;
    $("progress-text").textContent = `${done} of ${boxes.length} done`;
  }

  function renderPlan(plan) {
    currentPlan = plan;
    const { request } = plan;
    storageKey = `event-planner:${request.event_type}:${request.event_date}:${request.title}`;
    const checked = loadChecked();
    const money = moneyFormatter(request.currency);

    renderSummary(plan, money);
    renderBudget(plan, money);
    renderTimeline(plan, checked);
    renderVendors(plan, checked);
    renderIdeas(plan);
    updateProgress();

    results.hidden = false;
    results.focus();
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ------------------------------------------------------------------- events

  results.addEventListener("change", (event) => {
    const box = event.target;
    if (!(box instanceof HTMLInputElement) || box.type !== "checkbox") return;
    const state = loadChecked();
    state[box.dataset.id] = box.checked;
    saveChecked(state);
    updateProgress();
  });

  $("event_type").addEventListener("change", (event) => {
    const hints = PLACEHOLDERS[event.target.value];
    $("title").placeholder = hints.title;
    $("preferences").placeholder = hints.preferences;
  });

  $("print-btn").addEventListener("click", () => window.print());

  $("download-btn").addEventListener("click", () => {
    if (!currentPlan) return;
    const blob = new Blob([JSON.stringify(currentPlan, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = h("a", { attrs: { href: url, download: "event-plan.json" } });
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    formError.hidden = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating your plan...";
    form.setAttribute("aria-busy", "true");

    const data = Object.fromEntries(new FormData(form));
    const payload = {
      event_type: data.event_type,
      title: data.title.trim(),
      event_date: data.event_date,
      guest_count: Number.parseInt(data.guest_count, 10),
      total_budget: Number.parseFloat(data.total_budget),
      currency: data.currency,
      location: data.location.trim(),
      preferences: data.preferences.trim(),
    };

    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(describeError(response.status, body));
      renderPlan(body);
    } catch (error) {
      const offline = error instanceof TypeError; // fetch rejects with TypeError when offline
      formError.textContent = offline
        ? "Could not reach the server. Check your connection and try again."
        : error.message;
      formError.hidden = false;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Create my plan";
      form.removeAttribute("aria-busy");
    }
  });

  // Default the date to 90 days from now and block past dates.
  const soon = new Date();
  soon.setDate(soon.getDate() + 1);
  $("event_date").min = isoDate(soon);
  soon.setDate(soon.getDate() + 89);
  $("event_date").value = isoDate(soon);
})();
