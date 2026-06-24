const loginForm = document.getElementById("login-form");
const loginButton = document.getElementById("login-btn");

loginForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !password) {
    alert("Preencha todos os campos.");
    return;
  }

  try {
    loginButton.classList.add("loading");
    loginButton.textContent = "Entrando...";

    const data = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: email,
        password: password
      })
    });

    console.log("Resposta do login:", data);

    if (data.user && data.user.is_admin === true) {
      window.location.href = "admin.html";
      return;
    }

    window.location.href = "index.html";

  } catch (error) {
    console.error("Erro no login:", error);
    alert("Erro no login: " + error.message);

  } finally {
    loginButton.classList.remove("loading");
    loginButton.textContent = "Entrar";
  }
});