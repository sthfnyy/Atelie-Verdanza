let currentQty = 1;
let currentProduct = null;

function formatPrice(price) {
  return Number(price).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });
}

function getProductImage(product) {
  return product.image || "resources/images/arranjo1.jpg";
}

function getProductStatus(product) {
  const stock = Number(product.stock || 0);

  if (stock <= 0) {
    return "Esgotado";
  }

  if (stock <= 3) {
    return "Esgotando";
  }

  return "Em estoque";
}

async function loadProduct() {
  try {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");

    if (!id) {
      alert("Produto não encontrado.");
      window.location.href = "catalogo.html";
      return;
    }

    const data = await apiRequest(`/products/${id}`);

    currentProduct = data;

    renderProduct();

  } catch (error) {
    console.error("Erro ao carregar produto:", error);
    alert("Erro ao carregar produto.");
    window.location.href = "catalogo.html";
  }
}

function renderProduct() {
  if (!currentProduct) return;

  const productImage = getProductImage(currentProduct);

  document.title = `${currentProduct.name} — Ateliê Verdanza`;

  const titleEl = document.querySelector(".product-title");
  if (titleEl) {
    titleEl.textContent = currentProduct.name;
  }

  const priceEl = document.querySelector(".price-current");
  if (priceEl) {
    priceEl.textContent = formatPrice(currentProduct.price);
  }

  const descEl = document.querySelector(".product-description");
  if (descEl) {
    descEl.textContent =
      currentProduct.description || "Sem descrição disponível.";
  }

  const mainImage = document.getElementById("main-image");
  if (mainImage) {
    mainImage.src = productImage;
    mainImage.alt = currentProduct.name;
  }

  const thumbs = document.querySelectorAll(".gallery-thumb img");

  thumbs.forEach(img => {
    img.src = productImage;
    img.alt = currentProduct.name;
  });

  const categoryEl = document.getElementById("feature-category");
  if (categoryEl) {
    categoryEl.textContent = currentProduct.category || "—";
  }

  const statusEl = document.getElementById("feature-status");
  if (statusEl) {
    statusEl.textContent = getProductStatus(currentProduct);
  }
}

function increaseQty() {
  currentQty++;

  const qtyEl = document.getElementById("qty");

  if (qtyEl) {
    qtyEl.textContent = currentQty;
  }
}

function decreaseQty() {
  if (currentQty > 1) {
    currentQty--;
  }

  const qtyEl = document.getElementById("qty");

  if (qtyEl) {
    qtyEl.textContent = currentQty;
  }
}

function selectImage(index) {
  const thumbs = document.querySelectorAll(".gallery-thumb");

  thumbs.forEach(thumb => {
    thumb.classList.remove("active");
  });

  if (thumbs[index]) {
    thumbs[index].classList.add("active");
  }
}

function addToCart() {
  if (!currentProduct) return;

  const cart = JSON.parse(localStorage.getItem("cart")) || [];

  const existing = cart.find(item => Number(item.id) === Number(currentProduct.id));

  if (existing) {
    existing.quantity += currentQty;
  } else {
    cart.push({
      id: currentProduct.id,
      name: currentProduct.name,
      price: currentProduct.price,
      image: getProductImage(currentProduct),
      img: getProductImage(currentProduct),
      quantity: currentQty
    });
  }

  localStorage.setItem("cart", JSON.stringify(cart));

  if (typeof window.showToast === "function") {
    window.showToast(`${currentProduct.name} (${currentQty}x) adicionado ao carrinho`);
  } else {
    alert(`${currentProduct.name} (${currentQty}x) adicionado ao carrinho`);
  }

  currentQty = 1;

  const qtyEl = document.getElementById("qty");

  if (qtyEl) {
    qtyEl.textContent = currentQty;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  loadProduct();
});