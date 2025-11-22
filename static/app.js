// ---------- CONFIG ----------
const API_BASE = "/products";

const CATEGORY_LABELS = {
  fruits_veg: "Fruits & vegetables",
  bakery: "Bakery",
  dairy: "Dairy",
  meat: "Meat & fish",
  drinks: "Drinks",
  other: "Other",
};

// ---------- STATE ----------
let products = [];
let activeCategory = "all";
let searchQuery = "";
let editingProductId = null;

// ---------- DOM ----------
const form = document.getElementById("product-form");
const nameInput = document.getElementById("name-input");
const quantityInput = document.getElementById("quantity-input");
const categorySelect = document.getElementById("category-select");

const resetBtn = document.getElementById("reset-btn");

const searchInput = document.getElementById("search-input");
const categoryTabs = document.querySelectorAll("#category-filters [data-category]");

const productListEl = document.getElementById("product-list");
const emptyStateEl = document.getElementById("empty-state");

const itemsCountEl = document.getElementById("total-count");
const purchasedCountEl = document.getElementById("purchased-count");

// ---------- HELPERS ----------
function showError(message) {
  alert(message || "Something went wrong. Please try again.");
}

function updateSummary() {
  const totalItems = products.length;
  const purchasedItems = products.filter((p) => p.purchased).length;

  if (itemsCountEl) itemsCountEl.textContent = `${totalItems} items`;
  if (purchasedCountEl) purchasedCountEl.textContent = `${purchasedItems} purchased`;
}

// ---------- RENDER ----------
function renderProducts() {
  if (!productListEl) return;

  const filtered = products.filter((p) => {
    const matchesCategory =
      activeCategory === "all" || p.category === activeCategory;
    const matchesSearch =
      !searchQuery ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  productListEl.innerHTML = "";

  if (filtered.length === 0) {
    if (emptyStateEl) emptyStateEl.style.display = "block";
    updateSummary();
    return;
  } else {
    if (emptyStateEl) emptyStateEl.style.display = "none";
  }

  filtered.forEach((product) => {
    const li = document.createElement("li");
    li.className = "product-item";
    if (product.purchased) {
      li.classList.add("product-item--purchased");
    }

    // левая часть – клик по ней меняет статус (куплено / не куплено)
    const main = document.createElement("div");
    main.className = "product-main";
    main.addEventListener("click", () => togglePurchased(product));

    const title = document.createElement("div");
    title.className = "product-title";
    title.textContent = product.name;

    const meta = document.createElement("div");
    meta.className = "product-meta";
    const categoryLabel =
      CATEGORY_LABELS[product.category] || CATEGORY_LABELS.other;
    meta.textContent = `${product.quantity || "1"} pcs • ${categoryLabel}`;

    main.appendChild(title);
    main.appendChild(meta);

    // правая часть – статус + кнопки
    const actions = document.createElement("div");
    actions.className = "product-actions";

    const status = document.createElement("span");
    status.className =
      "product-badge " +
      (product.purchased ? "product-badge--purchased" : "product-badge--planned");
    status.textContent = product.purchased ? "Purchased" : "To buy";

    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.className = "icon-btn";
    editBtn.innerHTML = "✏️";
    editBtn.title = "Edit";
    editBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      startEdit(product);
    });

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "icon-btn icon-btn--danger";
    deleteBtn.innerHTML = "🗑";
    deleteBtn.title = "Delete";
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteProduct(product);
    });

    actions.appendChild(status);
    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    li.appendChild(main);
    li.appendChild(actions);

    productListEl.appendChild(li);
  });

  updateSummary();
}

// ---------- API ----------
async function loadProducts() {
  try {
    const res = await fetch(API_BASE);
    if (!res.ok) throw new Error("Failed to load");
    products = await res.json();
    renderProducts();
  } catch (err) {
    console.error(err);
    showError("Failed to load products.");
  }
}

async function createProduct(data) {
  try {
    const res = await fetch(API_BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create");
    const result = await res.json(); // { id: ... }
    products.push({ id: result.id, ...data });
    renderProducts();
  } catch (err) {
    console.error(err);
    showError("Something went wrong while saving the product.");
  }
}

async function saveProduct(product) {
  try {
    const res = await fetch(`${API_BASE}/${product.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(product),
    });
    if (!res.ok) throw new Error("Failed to update");

    // сервер возвращает {status: "updated"}, обновляем локально
    const idx = products.findIndex((p) => p.id === product.id);
    if (idx !== -1) products[idx] = product;
    renderProducts();
  } catch (err) {
    console.error(err);
    showError("Something went wrong while updating the product.");
  }
}

async function deleteProduct(product) {
  if (!confirm(`Delete "${product.name}" from your list?`)) return;

  try {
    const res = await fetch(`${API_BASE}/${product.id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete");
    products = products.filter((p) => p.id !== product.id);
    renderProducts();
  } catch (err) {
    console.error(err);
    showError("Something went wrong while deleting the product.");
  }
}

async function togglePurchased(product) {
  const updated = { ...product, purchased: !product.purchased };
  await saveProduct(updated);
}

// ---------- FORM ----------
function resetForm() {
  if (!form) return;
  form.reset();
  if (quantityInput) quantityInput.value = "1";
  editingProductId = null;
}

function startEdit(product) {
  editingProductId = product.id;
  if (nameInput) nameInput.value = product.name;
  if (quantityInput) quantityInput.value = product.quantity || "1";
  if (categorySelect) categorySelect.value = product.category || "other";
}

if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = (nameInput?.value || "").trim();
    const quantity = (quantityInput?.value || "").trim() || "1";
    const category = categorySelect?.value || "other";

    if (!name) {
      showError("Please enter a product name.");
      return;
    }

    const payload = {
      name,
      quantity,
      category,
      purchased: false,
    };

    if (editingProductId != null) {
      payload.id = editingProductId;
      const original = products.find((p) => p.id === editingProductId);
      payload.purchased = original ? original.purchased : false;
      await saveProduct(payload);
    } else {
      await createProduct(payload);
    }

    resetForm();
  });
}

if (resetBtn) {
  resetBtn.addEventListener("click", (e) => {
    e.preventDefault();
    resetForm();
  });
}

// ---------- FILTERS ----------
if (searchInput) {
  searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value;
    renderProducts();
  });
}

categoryTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    categoryTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    activeCategory = tab.dataset.category || "all";
    renderProducts();
  });
});

// ---------- INIT ----------
document.addEventListener("DOMContentLoaded", () => {
  resetForm();
  loadProducts();
});
