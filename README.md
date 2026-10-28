# Halcyon Supply Chain Fulfilment API

**Ticket:** HS-2026-0872

A Django REST Framework API for managing products, warehouses, stock levels, and fulfilment orders. The application uses JWT authentication, role-based permissions, PostgreSQL, Docker Compose, and automatic OpenAPI documentation.

## Features

- Product, warehouse, stock-level, and fulfilment-order endpoints.
- JWT access and refresh tokens.
- Role-based permissions for administrators and standard users.
- Product and warehouse relationships, stock validation, and database constraints.
- Standardized JSON error responses.
- Health monitoring with database connectivity and uptime.
- Swagger UI and OpenAPI schema.
- PostgreSQL persistence using Docker Compose.
- Automated linting, testing, coverage checks, and Docker image builds with GitHub Actions.

## Requirements

- Docker Desktop with Docker Compose.
- Git, if cloning the repository.

## Run locally with Docker Compose

1. Clone the repository:

   ```bash
   git clone https://github.com/khanyiso2/halcyon-supply-chain-api.git
   cd halcyon-supply-chain-api
   ```

2. Create your environment file from the example:

   **PowerShell:**

   ```powershell
   Copy-Item .env.example .env
   ```

3. Edit `.env` and replace the example values for `DJANGO_SECRET_KEY` and `DB_PASSWORD` with strong, unique values. Never commit `.env`.

4. Build and start the application:

   ```bash
   docker compose up --build -d
   ```

5. Check the service health:

   ```bash
   curl http://127.0.0.1:8000/health/
   ```

6. Open the API documentation:
   - Swagger UI: http://127.0.0.1:8000/api/docs/
   - OpenAPI schema: http://127.0.0.1:8000/api/schema/
   - Health endpoint: http://127.0.0.1:8000/health/

To stop the application:

```bash
docker compose down
```

To stop it and delete the PostgreSQL data volume:

```bash
docker compose down -v
```

**Warning:** The second command permanently deletes the database data stored in the Compose volume.

## Authentication

Obtain JWT tokens:

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USERNAME","password":"YOUR_PASSWORD"}'
```

Use the returned access token for authenticated requests:

```bash
curl http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Refresh an access token:

```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"YOUR_REFRESH_TOKEN"}'
```

Create an administrator account inside the running application container:

```bash
docker compose exec web python manage.py createsuperuser
```

Standard users can read the product and warehouse resources but cannot create, update, or delete those resources. Users can access their own fulfilment orders; administrators can manage all orders.

## API endpoints

| Method                  | Endpoint                  | Purpose                           |
| ----------------------- | ------------------------- | --------------------------------- |
| GET                     | `/health/`                | Health and database status        |
| POST                    | `/api/token/`             | Obtain JWT tokens                 |
| POST                    | `/api/token/refresh/`     | Refresh an access token           |
| GET, POST               | `/api/products/`          | List and create products          |
| GET, PUT, PATCH, DELETE | `/api/products/{id}/`     | Retrieve and manage a product     |
| GET, POST               | `/api/warehouses/`        | List and create warehouses        |
| GET, PUT, PATCH, DELETE | `/api/warehouses/{id}/`   | Retrieve and manage a warehouse   |
| GET, POST               | `/api/stock-levels/`      | List and create stock levels      |
| GET, PUT, PATCH, DELETE | `/api/stock-levels/{id}/` | Retrieve and manage a stock level |
| GET, POST               | `/api/orders/`            | List and create fulfilment orders |
| GET, PUT, PATCH, DELETE | `/api/orders/{id}/`       | Retrieve and manage an order      |
| GET                     | `/api/schema/`            | OpenAPI schema                    |
| GET                     | `/api/docs/`              | Swagger UI                        |

Authenticated access is required for the API resources. Write permissions depend on the resource and the user's role or ownership. The order endpoint supports creating an order, but order items are currently represented as read-only nested data.

## Filtering, searching, and ordering

The API supports configured filtering, searching, and ordering on relevant resources. Use the Swagger documentation to inspect the available query parameters.

Example:

```bash
curl "http://127.0.0.1:8000/api/products/?search=keyboard" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Database design and indexes

- **Product:** Unique indexed SKU and indexed name to support product lookup and searching.
- **Warehouse:** Unique warehouse code to prevent duplicate identifiers.
- **StockLevel:** Unique product–warehouse combination and a composite index on warehouse and product for stock queries.
- **FulfilmentOrder:** Indexed status for filtering orders by fulfilment state.
- **OrderItem:** Unique order–product combination to prevent duplicate product lines in one order.
- **Validation and constraints:** Non-negative prices, positive order-item quantities, non-negative stock quantities, and reserved stock that cannot exceed available quantity.

## Run tests and coverage

Activate your Python virtual environment and install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the tests:

```bash
python -m pytest supply_chain/tests.py -q
```

Run coverage:

```bash
python -m pytest --cov=supply_chain --cov-report=term-missing --cov-fail-under=80
```

Run linting:

```bash
python -m flake8 config supply_chain --exclude=supply_chain/migrations --max-line-length=120 --extend-ignore=E203,W503
```

## Continuous integration

The GitHub Actions workflow at `.github/workflows/ci.yml` runs Python linting and tests against PostgreSQL, enforces the configured coverage threshold, and builds the Docker image.

## Error responses

API errors use a consistent JSON structure containing an `error` object with the HTTP status code and message.

## Technology stack

- Python and Django
- Django REST Framework
- Simple JWT
- PostgreSQL
- Docker and Docker Compose
- drf-spectacular / OpenAPI
- pytest, pytest-cov, and Flake8
- GitHub Actions
