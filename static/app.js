const form = document.getElementById("search-form");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const bannerEl = document.getElementById("banner");
const sortBar = document.getElementById("sort-bar");

let lastSuppliers = [];
let currentSort = "score";

function extractFirstNumber(text) {
  if (!text) return null;
  const match = text.replace(/\s/g, "").match(/\d+([.,]\d+)?/);
  if (!match) return null;
  return parseFloat(match[0].replace(",", "."));
}

function sortSuppliers(suppliers, mode) {
  const arr = [...suppliers];
  if (mode === "price") {
    arr.sort((a, b) => {
      const pa = extractFirstNumber(a.price_info);
      const pb = extractFirstNumber(b.price_info);
      if (pa === null && pb === null) return 0;
      if (pa === null) return 1;
      if (pb === null) return -1;
      return pa - pb;
    });
  } else if (mode === "confidence") {
    arr.sort((a, b) => b.confidence - a.confidence);
  } else {
    arr.sort((a, b) => b.score - a.score);
  }
  return arr;
}

function field(label, value, isLink) {
  if (!value) return "";
  const v = isLink
    ? `<a href="${value}" target="_blank" rel="noopener">${value}</a>`
    : value;
  return `<div class="row"><span class="k">${label}</span><span class="v">${v}</span></div>`;
}

function renderCard(s) {
  const scorePct = Math.round(s.score * 100);
  const contacts = [s.phone, s.email, s.other_contacts].filter(Boolean).join(" · ");
  return `
    <div class="card ${s.recommended ? "recommended" : ""}">
      ${s.recommended ? '<span class="badge">Рекомендуем</span>' : ""}
      <h3>${s.name}</h3>
      ${s.description ? `<div class="desc">${s.description}</div>` : ""}
      ${field("Регион", s.region)}
      ${field("Контакты", contacts || null)}
      ${field("Мин. заказ", s.min_order)}
      ${field("Цена", s.price_info)}
      ${field("Сертификаты", s.certificates)}
      ${field("Доставка", s.delivery_terms)}
      ${field("Заметки", s.notes)}
      <div class="score-bar"><div style="width:${scorePct}%"></div></div>
      <div class="card-links">
        ${s.website ? `<a href="${s.website}" target="_blank" rel="noopener">Сайт →</a>` : ""}
        ${s.source_url ? `<a href="${s.source_url}" target="_blank" rel="noopener">Источник →</a>` : ""}
      </div>
    </div>
  `;
}

function render(suppliers) {
  resultsEl.innerHTML = sortSuppliers(suppliers, currentSort).map(renderCard).join("");
}

sortBar.addEventListener("click", (e) => {
  const btn = e.target.closest(".sort-btn");
  if (!btn) return;
  document.querySelectorAll(".sort-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  currentSort = btn.dataset.sort;
  render(lastSuppliers);
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    category: document.getElementById("category").value.trim(),
    region: document.getElementById("region").value.trim(),
    keywords: document.getElementById("keywords").value.trim(),
    limit: parseInt(document.getElementById("limit").value, 10),
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Ищем...";
  bannerEl.classList.add("hidden");
  sortBar.classList.add("hidden");
  resultsEl.innerHTML = "";
  statusEl.textContent = "ИИ гуглит и анализирует поставщиков — это может занять до 30 секунд...";

  try {
    const resp = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(`Сервер вернул ${resp.status}`);
    const data = await resp.json();

    lastSuppliers = data.suppliers;
    statusEl.textContent = data.suppliers.length
      ? `Найдено: ${data.suppliers.length}${data.cached ? " (из кэша)" : ""}`
      : "Ничего не найдено, попробуйте изменить запрос.";

    if (data.warning) {
      bannerEl.textContent = data.warning;
      bannerEl.classList.remove("hidden");
    }
    if (data.suppliers.length) {
      sortBar.classList.remove("hidden");
    }
    render(lastSuppliers);
  } catch (err) {
    statusEl.textContent = `Ошибка: ${err.message}`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Найти поставщиков";
  }
});
