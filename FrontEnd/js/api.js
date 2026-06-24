const API_PORT = 3001;
const API_HOST = (typeof window !== 'undefined' && window.location && window.location.hostname)
  ? window.location.hostname
  : 'localhost';

const API_URL = `http://${API_HOST}:${API_PORT}/api`;
const BASE_URL = `http://${API_HOST}:${API_PORT}`;

function getToken() {
  return sessionStorage.getItem("token");
}

function setToken(token) {
  sessionStorage.setItem("token", token);
}

function removeToken() {
  sessionStorage.removeItem("token");
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/[.$?*|{}()\[\]\\\/\+^]/g, '\\$&') + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

async function ensureCsrfToken() {
  let token = getCookie('csrfToken');
  if (token) return token;

  const response = await fetch(`${API_URL}/auth/csrf`, {
    method: 'GET',
    credentials: 'include'
  });

  const data = await response.json();

  token = data.csrfToken || getCookie('csrfToken');

  return token;
}

async function apiRequest(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers
  };

  const method = (options.method || 'GET').toUpperCase();
  const isSafeMethod = ['GET', 'HEAD', 'OPTIONS'].includes(method);

  if (!isSafeMethod) {
    const csrfToken = await ensureCsrfToken();

    if (!csrfToken) {
      throw new Error("Não foi possível obter o token CSRF.");
    }

    headers['X-CSRF-Token'] = csrfToken;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include'
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Erro na requisição.");
  }

  return data;
}

// Demonstração de request SÍNCRONO real (Fetch não suporta sync).
// Ative abrindo qualquer página que carregue este arquivo com `?syncDemo=1`.
function syncHealthCheck() {
  const xhr = new XMLHttpRequest();
  xhr.open('GET', `${BASE_URL}/`, false);

  try {
    xhr.send(null);
  } catch (error) {
    return {
      ok: false,
      error: error?.message || 'Erro ao executar XHR síncrono.'
    };
  }

  const ok = xhr.status >= 200 && xhr.status < 300;

  if (!ok) {
    return {
      ok: false,
      status: xhr.status,
      body: xhr.responseText
    };
  }

  try {
    return JSON.parse(xhr.responseText);
  } catch (_) {
    return {
      ok: true,
      body: xhr.responseText
    };
  }
}

(function maybeRunSyncDemo() {
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.has('syncDemo')) {
      console.log('[SYNC DEMO] Resultado:', syncHealthCheck());
    }
  } catch (_) {
    // noop
  }
})();