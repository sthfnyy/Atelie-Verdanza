

# 🌿 Ateliê Verdanza — FrontEnd

FrontEnd do e-commerce Ateliê Verdanza, desenvolvido com HTML, CSS e JavaScript.

## Tecnologias

- HTML5
- CSS3
- JavaScript
- Fetch API
- LocalStorage
- Cookies HTTP

## Funcionalidades

- Página inicial
- Catálogo de produtos
- Página de detalhes do produto
- Carrinho com LocalStorage
- Cadastro de usuário
- Login
- Logout
- Painel administrativo
- Consumo da API do BackEnd

## Como rodar

Antes de iniciar o FrontEnd, o BackEnd deve estar rodando em:

```text
http://localhost:3001
```

Depois, abra um terminal na pasta `FrontEnd`:

```bash
cd FrontEnd
python3 -m http.server 5500
```

Acesse no navegador:

```text
http://localhost:5500/index.html
```

## Páginas principais

```text
http://localhost:5500/index.html
http://localhost:5500/catalogo.html
http://localhost:5500/produto.html?id=1
http://localhost:5500/carrinho.html
http://localhost:5500/cadastro.html
http://localhost:5500/login.html
http://localhost:5500/admin.html
```

## Observação

Não abra os arquivos diretamente com `file:///`.

Use sempre:

```text
http://localhost:5500
```

Isso é necessário para o funcionamento correto de cookies, CORS, autenticação e CSRF.