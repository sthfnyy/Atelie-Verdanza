/* ── COMPONENTES REUTILIZÁVEIS ── */

/**
 * Renderiza o header/ Menu de navegação
 */
function renderNav() {
  const nav = document.querySelector('nav'); // procura no html <nav></nav>
  if (!nav) return;

  //coloca no Html dentro da tag <nav> o código abaixo
  nav.innerHTML = ` 
    <a href="index.html" class="nav-logo">Ateliê verdanza</a>
    <ul class="nav-links">
      <li><a href="index.html" class="${getCurrentPage() === 'index' ? 'active' : ''}">Home</a></li>
      <li><a href="catalogo.html" class="${getCurrentPage() === 'catalogo' ? 'active' : ''}">Catálogo</a></li>
      <li><a href="about.html" class="${getCurrentPage() === 'about' ? 'active' : ''}">Sobre</a></li>
    </ul>
    <div class="nav-actions">
      <button class="nav-icon" title="Carrinho" onclick="window.location.href='carrinho.html'">
        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
        </svg>
        <span class="cart-badge" id="nav-badge">0</span>
      </button>
      <button class="nav-icon" title="Conta" onclick="window.location.href='login.html'">
        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
      </button>
    </div>
  `;
}

/**
 * Renderiza o footer/Rodapé
 */
function renderFooter() {
  const footer = document.querySelector('footer');
  if (!footer) return;

  footer.innerHTML = `
    <div class="footer-top">
      <div class="footer-brand">
        <h3>Ateliê verdanza</h3>
        <p>Compartilhando um futuro mais verde, uma folha de cada vez. Junte-se a nós em nossa jornada de orgânicos.</p>
        <div class="footer-socials">
        </div>
      </div>

      <div class="footer-col">
        <h4>Menu</h4>
        <ul>
          <li><a href="index.html">Home</a></li>
          <li><a href="catalogo.html">Catálogo</a></li>
          <li><a href="about.html">Sobre</a></li>
          <li><a href="#">Contato</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h4>Fale conosco</h4>
        <address>
          Bairro Jorge, Rua 40<br />
          Piso 4º, Rio 12<br />
          Seg a Sab, 10h às 18h
        </address>
      </div>
    </div>

    <div class="footer-bottom">
      <p>© 2024 Ateliê verdanza. Todos os direitos reservados.</p>
      <div class="footer-bottom-links">
        <a href="login.html">Termos de Serviço</a>
        <a href="#">Formatos de Páginas</a>
      </div>
    </div>
  `;
}

/**
 * Obtém a página atual baseado no nome do arquivo
 */
function getCurrentPage() {
  const path = window.location.pathname;
  if (path.includes('index')) return 'index';
  if (path.includes('catalogo')) return 'catalogo';
  if (path.includes('carrinho')) return 'carrinho';
  if (path.includes('about')) return 'about';
  if (path.includes('produto')) return 'produto';
  if (path.includes('login')) return 'login';
  if (path.includes('admin')) return 'admin';
  return 'index';
}

/**
 * Exibe notificação (toast) / mensagem temporária
 */
function showToast(message) {
  const toast = document.getElementById('toast') || createToastElement();
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
}

/**
 * Cria elemento de toast se não existir
 */
function createToastElement() {
  const toast = document.createElement('div');
  toast.id = 'toast';
  toast.className = 'toast';
  document.body.appendChild(toast);
  return toast;
}

/**
 * Inicializa componentes globais
 */
function initComponents() {
  renderNav();
  renderFooter();
}

// Auto-inicializar quando o DOM estiver pronto
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initComponents);
} else {
  initComponents();
}

// Funções do carrinho
function getCart() {
  return JSON.parse(localStorage.getItem('cart')) || [];
}

function saveCart(cart) {
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
}

//Contador do carrinho
function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];

  const totalItems = cart.reduce((total, item) => {
    return total + Number(item.quantity || 1);
  }, 0);

const counters = document.querySelectorAll('#nav-badge, .cart-badge, .cart-count, #cart-count, [data-cart-count]');
  counters.forEach(counter => {
    counter.textContent = totalItems;
    counter.style.display = totalItems > 0 ? 'inline-flex' : 'none';
  });
}

document.addEventListener('DOMContentLoaded', updateCartCount);


function addToCart(product, quantity = 1) {
  const cart = getCart();

  const productId = String(product.id);
  const existingItem = cart.find(item => String(item.id) === productId);

  if (existingItem) {
    existingItem.quantity += Number(quantity);
  } else {
    cart.push({
      id: product.id,
      name: product.name || product.nome,
      price: Number(product.price || product.preco || 0),
      img: product.img || product.image || product.imagem || '',
      quantity: Number(quantity)
    });
  }

  saveCart(cart);
}

document.addEventListener('DOMContentLoaded', updateCartCount);


/**
 * 1. Menu de navegação
 * 2. Rodapé
 * 3. Toast de mensagens
 * 4. Contador do carrinho
 * 5. Funções do carrinho
 * 6. Card de produto
 * 7. Botão de adicionar ao carrinho
 */
