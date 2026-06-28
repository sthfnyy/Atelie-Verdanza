console.log("admin.js carregado");

let products = [];
let deleteTarget = null;
let editingProductId = null;

let orders = [];
let clients = [];

const orderStatusBadge = {
  pendente: '<span class="status-badge status-pendente">Pendente</span>',
  enviado: '<span class="status-badge status-enviado">Pronto para Retirada</span>',
  entregue: '<span class="status-badge status-entregue">Entregue</span>',
};

function renderOrderStatusSelect(order) {
  if (order.status === 'entregue') {
    return `<span class="status-badge status-entregue">Entregue</span>`;
  }
  const options = [
    { value: 'pendente', label: 'Pendente' },
    { value: 'enviado', label: 'Pronto para Retirada' },
    { value: 'entregue', label: 'Entregue' }
  ];
  return `
    <select class="status-badge status-${order.status}" onchange="changeOrderStatus(${order.dbId}, this.value)" style="border: none; font-family: inherit; font-size: 0.72rem; font-weight: inherit; cursor: pointer; outline: none; padding: 4px 8px; border-radius: 12px; background: transparent; color: inherit;">
      ${options.map(opt => `<option value="${opt.value}" ${order.status === opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}
    </select>
  `;
}

async function changeOrderStatus(dbId, status) {
  try {
    await apiRequest(`/orders/${dbId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status })
    });
    showToast("Status do pedido atualizado com sucesso!");
    await carregarPedidosAdmin();
    renderAllOrders();
  } catch (error) {
    console.error("Erro ao atualizar status:", error);
    showToast("Erro ao atualizar status: " + error.message);
  }
}

async function carregarPedidosAdmin() {
  try {
    const data = await apiRequest("/orders");
    orders = data.map(order => ({
      id: `#ORD-${order.id}`,
      dbId: order.id,
      client: order.client_name,
      items: order.items_count,
      total: `R$ ${order.total_price.toFixed(2).replace(".", ",")}`,
      status: order.status,
      rawItems: order.items
    }));
    renderRecentOrders();
    updateOrderDashboardStats();
  } catch (error) {
    console.error("Erro ao carregar pedidos:", error);
    showToast("Erro ao carregar pedidos: " + error.message);
  }
}

function showOrderDetails(dbId) {
  const order = orders.find(o => o.dbId === dbId);
  if (!order) return;

  const modalId = `order-details-modal-${dbId}`;
  
  const existing = document.getElementById(modalId);
  if (existing) existing.remove();

  const itemsHtml = (order.rawItems || []).map(item => `
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem;">
      <div style="display: flex; flex-direction: column;">
        <span style="font-weight: 500; color: var(--text-dark);">${item.product_name}</span>
        <span style="font-size: 0.72rem; color: var(--text-light);">Preço unitário: R$ ${item.price.toFixed(2).replace(".", ",")}</span>
      </div>
      <div style="text-align: right;">
        <span style="font-weight: 400; color: var(--text-mid); margin-right: 16px;">x${item.quantity}</span>
        <span style="font-weight: 500; color: var(--text-dark);">R$ ${(item.price * item.quantity).toFixed(2).replace(".", ",")}</span>
      </div>
    </div>
  `).join('');

  const modalHtml = `
    <div id="${modalId}" class="modal-overlay open" style="z-index: 2000; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
      <div class="modal" style="background: white; border-radius: 12px; width: 90%; max-width: 500px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); box-sizing: border-box;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 12px;">
          <h3 style="font-family: 'Cormorant Garamond', serif; font-size: 1.6rem; font-weight: 500; color: var(--text-dark); margin: 0;">Detalhes do Pedido</h3>
          <span style="font-size: 0.8rem; font-weight: 500; background: var(--cream); padding: 4px 10px; border-radius: 20px; color: var(--text-dark);">${order.id}</span>
        </div>
        
        <div style="margin-bottom: 24px; font-size: 0.85rem; color: var(--text-mid); display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div>
            <strong style="display: block; color: var(--text-light); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Cliente</strong>
            <span style="color: var(--text-dark); font-weight: 400;">${order.client}</span>
          </div>
          <div>
            <strong style="display: block; color: var(--text-light); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Status</strong>
            <span style="text-transform: capitalize; color: var(--text-dark); font-weight: 400;">${order.status}</span>
          </div>
        </div>

        <h4 style="font-family: 'Jost', sans-serif; font-size: 0.78rem; font-weight: 500; color: var(--text-light); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; border-bottom: 1px solid var(--border); padding-bottom: 6px;">Itens Pedidos</h4>
        
        <div style="max-height: 240px; overflow-y: auto; margin-bottom: 24px; padding-right: 4px;">
          ${itemsHtml}
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; background: var(--warm-white); padding: 16px; border-radius: 8px; margin-bottom: 24px;">
          <span style="font-size: 0.85rem; font-weight: 400; color: var(--text-mid);">Total do Pedido</span>
          <span style="font-size: 1.2rem; font-weight: 600; color: var(--dark-green);">${order.total}</span>
        </div>

        <div style="display: flex; justify-content: flex-end;">
          <button onclick="document.getElementById('${modalId}').remove()" class="btn-primary" style="margin: 0; width: auto; padding: 10px 24px; font-size: 0.75rem; letter-spacing: 0.05em; height: auto;">Fechar</button>
        </div>
      </div>
    </div>
  `;

  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = modalHtml;
  document.body.appendChild(tempDiv.firstElementChild);
}

function updateOrderDashboardStats() {
  const totalOrdersEl = document.getElementById("stats-total-orders");
  const pendingOrdersEl = document.getElementById("stats-pending-orders");
  const totalRevenueEl = document.getElementById("stats-total-revenue");

  if (!totalOrdersEl || !pendingOrdersEl || !totalRevenueEl) return;

  const totalOrders = orders.length;
  const pendingOrders = orders.filter(o => o.status === "pendente").length;
  
  const revenue = orders.reduce((sum, order) => {
    const num = Number(order.total.replace("R$", "").replace(/\./g, "").replace(",", ".").trim());
    return sum + (isNaN(num) ? 0 : num);
  }, 0);

  totalOrdersEl.textContent = totalOrders;
  pendingOrdersEl.textContent = pendingOrders;
  totalRevenueEl.textContent = `R$ ${revenue.toFixed(2).replace(".", ",")}`;
}

async function carregarClientesAdmin() {
  try {
    const data = await apiRequest("/clients");
    clients = data;
    renderClients();
  } catch (error) {
    console.error("Erro ao carregar clientes:", error);
    showToast("Erro ao carregar clientes: " + error.message);
  }
}

function renderClients() {
  const tbody = document.getElementById("clients-tbody");
  if (!tbody) return;

  if (clients.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align:center;padding:24px;color:var(--text-light);font-size:.82rem;">
          Nenhum cliente cadastrado.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = clients.map(client => `
    <tr>
      <td>${client.name}</td>
      <td>${client.email}</td>
      <td>${client.orders_count}</td>
      <td>R$ ${client.total_spent.toFixed(2).replace(".", ",")}</td>
      <td>${client.last_purchase || '—'}</td>
    </tr>
  `).join("");
}

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
    await carregarPedidosAdmin();
    await carregarClientesAdmin();

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

        ${renderOrderStatusSelect(order)}
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
      <td>${renderOrderStatusSelect(order)}</td>
      <td>
        <button class="action-btn" title="Ver detalhes" onclick="showOrderDetails(${order.dbId})">
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
  } else if (name === "clientes") {
    renderClients();
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