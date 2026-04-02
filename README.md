# ShortCut API

API moderna de encurtamento de URLs com analytics de cliques e geração de QR Code, construída com FastAPI.

## Funcionalidades

- **Autenticação JWT** — registro e login seguros
- **Encurtamento de URLs** — gera códigos curtos aleatórios ou customizados
- **Redirecionamento** — acesse `/{code}` e seja redirecionado
- **Analytics** — rastreamento de cliques com IP, user-agent, referrer
- **QR Code** — gera imagem PNG do QR Code de qualquer link
- **Expiração** — links com data de expiração opcional

## Stack

- **FastAPI** + **Uvicorn** (async)
- **SQLAlchemy 2.0** (async) + **SQLite**
- **Pydantic v2** para validação
- **JWT** (python-jose) para autenticação
- **qrcode** para geração de QR Codes

## Como rodar

```bash
# Clone o repositório
git clone https://github.com/Kaylan00/shortcut-api.git
cd shortcut-api

# Crie o ambiente virtual
python -m venv venv
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Configure o .env
cp .env.example .env

# Rode a aplicação
uvicorn app.main:app --reload
```

Acesse a documentação interativa em: **http://localhost:8000/docs**

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Health check |
| `POST` | `/api/v1/users/register` | Criar conta |
| `POST` | `/api/v1/users/login` | Login (retorna JWT) |
| `GET` | `/api/v1/users/me` | Perfil do usuário logado |
| `POST` | `/api/v1/links` | Encurtar uma URL |
| `GET` | `/api/v1/links` | Listar meus links |
| `GET` | `/api/v1/links/{id}` | Detalhes de um link |
| `PATCH` | `/api/v1/links/{id}` | Editar link |
| `DELETE` | `/api/v1/links/{id}` | Deletar link |
| `GET` | `/api/v1/links/{id}/qrcode` | QR Code (PNG) |
| `GET` | `/api/v1/analytics/{id}` | Analytics do link |
| `GET` | `/{short_code}` | Redireciona para a URL original |

## Exemplo de uso

```bash
# Registrar
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "kaylan", "email": "kaylan@email.com", "password": "123456"}'

# Login
curl -X POST http://localhost:8000/api/v1/users/login \
  -d "username=kaylan&password=123456"

# Encurtar URL (use o token retornado no login)
curl -X POST http://localhost:8000/api/v1/links \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com/Kaylan00"}'
```

## Licença

MIT
