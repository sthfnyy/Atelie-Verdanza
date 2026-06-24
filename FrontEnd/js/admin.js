console.log("admin.js carregado");

let products = [];
let deleteTarget = null;
let editingProductId = null;

const orders = [
  { id: "#ORD-9022", client: "Beatriz Silveira", items: 2, total: "R$ 264,00", status: "pendente" },
  { id: "#ORD-9018", client: "Henrique Costa", items: 1, total: "R$ 89,00", status: "enviado" },
  { id: "#ORD-8995", client: "Mariana Luz", items: 3, total: "R$ 412,00", status: "entregue" },
  { id: "#ORD-8981", client: "Carlos Mendes", items: 1, total: "R$ 189,00", status: "entregue" },
];

const orderStatusBadge = {
  pendente: '<span class="status-badge status-pendente">Pendente ˅</span>',
  enviado: '<span class="status-badge status-enviado">Pronto para Retirada ˅</span>',
  entregue: '<span class="status-badge status-entregue">Entregue</span>',
};

function getProductStatus(product) {
  const stock = Number(product.stock || 0);

  if (stock <= 0) {
    return '<span class="badge badge-red"><span class="badge-dot"></span>Esgotado</span>';
  }

  if (stock <= 3) {
    return '<span class="badge badge-orange"><span class="badge-dot"></span>Esgotando</span>';
  }

  return '<span class="badge badge-green"><span class="badge-dot"></span>Em estoque</span>';
}

async function verificarAcessoAdmin() {
  try {
    const user = await apiRequest("/auth/profile");

    if (!user || user.is_admin !== true) {
      showToast("Acesso restrito a administradores.");

      setTimeout(() => {
        window.location.href = "login.html";
      }, 1200);

      return;
    }

    await carregarProdutosAdmin();
    renderRecentOrders();

  } catch (error) {
    console.error("Erro ao verificar admin:", error);

    showToast("Você precisa fazer login para acessar o painel.");

    setTimeout(() => {
      window.location.href = "login.html";
    }, 1200);
  }
}

async function carregarProdutosAdmin() {
  try {
    const data = await apiRequest("/products");

    products = data.map(product => ({
      id: product.id,
      name: product.name,
      description: product.description || "",
      category: product.category || "",
      price: Number(product.price),
      image: product.image || "resources/images/arranjo1.jpg",
      stock: Number(product.stock || 0),
    }));

    renderCatalog();

  } catch (error) {
    console.error("Erro ao carregar produtos:", error);
    showToast("Erro ao carregar produtos: " + error.message);
  }
}

function renderCatalog() {
  const tbody = document.getElementById("catalog-tbody");

  if (!tbody) return;

  if (products.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align:center;padding:24px;color:var(--text-light);font-size:.82rem;">
          Nenhum produto cadastrado.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = products.map(product => `
    <tr>
      <td>
        <div class="product-cell">
          <div class="product-thumb">
            <img src="${product.image}" alt="${product.name}" />
          </div>

          <div class="product-cell-info">
            <p class="name">${product.name}</p>
            <p class="sub">${product.category || product.description}</p>
          </div>
        </div>
      </td>

      <td>${getProductStatus(product)}</td>

      <td style="white-space:nowrap;">
        R$ ${product.price.toFixed(2).replace(".", ",")}
      </td>

      <td>
        <button class="action-btn" title="Editar" onclick="editProduct(${product.id})">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>

        <button class="action-btn del" title="Remover" onclick="askDelete(${product.id})">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6"/>
            <path d="M14 11v6"/>
            <path d="M9 6V4h6v2"/>
          </svg>
        </button>
      </td>
    </tr>
  `).join("");
}

async function saveProduct() {
  const name = document.getElementById("prod-nome").value.trim();
  const description = document.getElementById("prod-desc").value.trim();
  const price = parseFloat(document.getElementById("prod-preco").value);
  const category = document.getElementById("prod-cat").value;

  if (!name) {
    showToast("Informe o nome do produto.");
    return;
  }

  if (!price || price <= 0) {
    showToast("Informe um preço válido.");
    return;
  }

  const preview = document.getElementById("upload-preview");

  let image = "resources/images/arranjo1.jpg";

  if (preview && preview.style.display !== "none" && preview.src) {
    image = preview.src;
  }

  const productPayload = {
    name: name,
    description: description || category,
    price: price,
    image: image,
    category: category,
    stock: 10
  };

  console.log("Produto enviado para o backend:", productPayload);

  try {
    if (editingProductId !== null) {
      await apiRequest(`/products/${editingProductId}`, {
        method: "PUT",
        body: JSON.stringify(productPayload)
      });

      showToast(`"${name}" atualizado com sucesso.`);
    } else {
      await apiRequest("/products", {
        method: "POST",
        body: JSON.stringify(productPayload)
      });

      showToast(`"${name}" cadastrado com sucesso.`);
    }

    editingProductId = null;
    limparFormularioProduto();

    await carregarProdutosAdmin();

  } catch (error) {
    console.error("Erro ao salvar produto:", error);
    showToast("Erro ao salvar produto: " + error.message);
  }
}

function editProduct(id) {
  const product = products.find(item => Number(item.id) === Number(id));

  if (!product) {
    showToast("Produto não encontrado.");
    return;
  }

  editingProductId = product.id;

  document.getElementById("prod-nome").value = product.name;
  document.getElementById("prod-desc").value = product.description || "";
  document.getElementById("prod-preco").value = product.price;
  document.getElementById("prod-cat").value = product.category || "Plantas";

  const preview = document.getElementById("upload-preview");
  const uploadIcon = document.getElementById("upload-icon");
  const uploadText = document.getElementById("upload-text");

  if (preview && product.image) {
    preview.src = product.image;
    preview.style.display = "block";

    if (uploadIcon) uploadIcon.style.display = "none";
    if (uploadText) uploadText.style.display = "none";
  }

  document.querySelector(".card").scrollIntoView({ behavior: "smooth" });

  showToast("Editando produto. Faça as alterações e salve.");
}

function askDelete(id) {
  deleteTarget = id;

  const modal = document.getElementById("del-modal");

  if (modal) {
    modal.classList.add("open");
  }
}

function closeModal() {
  deleteTarget = null;

  const modal = document.getElementById("del-modal");

  if (modal) {
    modal.classList.remove("open");
  }
}

async function confirmDelete() {
  if (deleteTarget === null) return;

  try {
    await apiRequest(`/products/${deleteTarget}`, {
      method: "DELETE",
    });

    closeModal();
    await carregarProdutosAdmin();

    showToast("Produto removido com sucesso.");

  } catch (error) {
    console.error("Erro ao remover produto:", error);
    showToast("Erro ao remover produto: " + error.message);
  }
}

function limparFormularioProduto() {
  document.getElementById("prod-nome").value = "";
  document.getElementById("prod-desc").value = "";
  document.getElementById("prod-preco").value = "";
  document.getElementById("prod-cat").value = "Plantas";

  const preview = document.getElementById("upload-preview");
  const uploadIcon = document.getElementById("upload-icon");
  const uploadText = document.getElementById("upload-text");

  if (preview) {
    preview.style.display = "none";
    preview.src = "";
  }

  if (uploadIcon) uploadIcon.style.display = "";
  if (uploadText) uploadText.style.display = "";
}

function previewImage(event) {
  const file = event.target.files[0];

  if (!file) return;

  const reader = new FileReader();

  reader.onload = function (readerEvent) {
    const preview = document.getElementById("upload-preview");
    const uploadIcon = document.getElementById("upload-icon");
    const uploadText = document.getElementById("upload-text");

    preview.src = readerEvent.target.result;
    preview.style.display = "block";

    if (uploadIcon) uploadIcon.style.display = "none";
    if (uploadText) uploadText.style.display = "none";
  };

  reader.readAsDataURL(file);
}

function renderRecentOrders() {
  const recentOrdersList = document.getElementById("recent-orders-list");

  if (!recentOrdersList) return;

  recentOrdersList.innerHTML = orders.slice(0, 3).map(order => `
    <div class="order-card">
      <div class="order-top">
        <div>
          <p class="order-id">${order.id}</p>
          <p class="order-name">${order.client}</p>
        </div>

        <button class="order-menu-btn">⋯</button>
      </div>

      <div class="order-bottom">
        <span class="order-meta">
          ${order.items} ${order.items === 1 ? "Item" : "Itens"} • ${order.total}
        </span>

        ${orderStatusBadge[order.status]}
      </div>
    </div>
  `).join("");
}

function renderAllOrders() {
  const tbody = document.getElementById("all-orders-tbody");

  if (!tbody) return;

  tbody.innerHTML = orders.map(order => `
    <tr>
      <td style="font-weight:400;">${order.id}</td>
      <td>${order.client}</td>
      <td>${order.items}</td>
      <td>${order.total}</td>
      <td>${orderStatusBadge[order.status]}</td>
      <td>
        <button class="action-btn" title="Ver detalhes">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      </td>
    </tr>
  `).join("");
}

function showSection(name) {
  document.querySelectorAll(".section-panel").forEach(panel => {
    panel.classList.remove("active");
  });

  document.querySelectorAll(".nav-item").forEach(button => {
    button.classList.remove("active");
  });

  const selectedPanel = document.getElementById(`panel-${name}`);

  if (selectedPanel) {
    selectedPanel.classList.add("active");
  }

  const map = {
    produtos: 0,
    pedidos: 1,
    clientes: 2,
  };

  const navItems = document.querySelectorAll(".nav-item");

  if (navItems[map[name]]) {
    navItems[map[name]].classList.add("active");
  }

  if (name === "pedidos") {
    renderAllOrders();
  }
}

function showToast(message) {
  const toast = document.getElementById("toast");

  if (!toast) {
    alert(message);
    return;
  }

  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(window._toastTimeout);

  window._toastTimeout = setTimeout(() => {
    toast.classList.remove("show");
  }, 2800);
}

async function logoutAdmin() {
  if (!confirm("Deseja sair?")) return;

  try {
    await apiRequest("/auth/logout", {
      method: "POST",
    });

    showToast("Logout realizado com sucesso.");

    setTimeout(() => {
      window.location.href = "login.html";
    }, 800);

  } catch (error) {
    console.error("Erro ao sair:", error);
    showToast("Erro ao sair: " + error.message);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const modal = document.getElementById("del-modal");

  if (modal) {
    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        closeModal();
      }
    });
  }

  verificarAcessoAdmin();
});