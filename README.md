# Leeds Housing Market API

A production-ready RESTful API providing property listing data and market analytics for the Leeds housing market. Built with FastAPI and PostgreSQL, containerised with Docker, and deployed on Microsoft Azure.

## API Reference

**📄 [Download the complete API Documentation (PDF)](./API_Documentation.pdf)**

Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Table of Contents
- [Features](#features)
- [Technology Stack](#technology-stack)
- [API Reference](#api-reference)
  - [Listings Endpoints](#listings-endpoints)
  - [Analytics Endpoints](#analytics-endpoints)
- [Data Model](#data-model)
- [Authentication](#authentication)
- [Local Development](#local-development)
- [Running Tests](#running-tests)
- [Database Migrations](#database-migrations)
- [Deployment](#deployment)
- [Data Source](#data-source)

---

## Features

- **Full CRUD Operations** — Create, read, update and delete property listings
- **Market Analytics** — Aggregated market summaries and affordability calculations
- **Data Validation** — Strict input validation with UK postcode regex patterns
- **API Key Authentication** — Protected write operations with header-based authentication
- **Automatic Database Seeding** — Pre-populated with real Leeds property data on startup
- **Database Migrations** — Version-controlled schema management with Alembic
- **Containerised Development** — Docker Compose orchestration for local development
- **Cloud-Native Deployment** — Configured for Azure App Service with managed PostgreSQL

---

## Technology Stack

| Component            | Technology                                                 |
| -------------------- | ---------------------------------------------------------- |
| **Framework**        | Python 3.11 / FastAPI                                      |
| **Database**         | PostgreSQL 15                                              |
| **ORM**              | SQLAlchemy                                                 |
| **Migrations**       | Alembic                                                    |
| **Validation**       | Pydantic                                                   |
| **ASGI Server**      | Uvicorn                                                    |
| **Containerisation** | Docker / Docker Compose                                    |
| **Cloud Platform**   | Microsoft Azure (App Service + PostgreSQL Flexible Server) |
| **Testing**          | pytest / httpx                                             |
| **LLM Integration**  | Google Gemini API (Generative AI for smart search)         |

---

## API Reference

### Base URLs

| Environment           | URL                                                                               |
| --------------------- | --------------------------------------------------------------------------------- |
| **Production**        | `https://housing-project-api-bda2hwf3fzfvg0bb.francecentral-01.azurewebsites.net` |
| **Local Development** | `http://localhost:8000`                                                           |

Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

### Listings Endpoints

#### Get All Listings

Retrieve all property listings with pagination support.

```
GET /api/listings/
```

**Query Parameters:**

| Parameter | Type    | Default | Description                         |
| --------- | ------- | ------- | ----------------------------------- |
| `skip`    | integer | 0       | Number of records to skip           |
| `limit`   | integer | 100     | Maximum number of records to return |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/listings/?skip=0&limit=10" \
  -H "Accept: application/json"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "address": "14, Victoria Road",
    "postcode": "LS6 1PF",
    "price": 275000,
    "property_type": "Terraced",
    "bedrooms": 3
  }
]
```

---

#### Get Single Listing

Retrieve a specific property listing by its ID.

```
GET /api/listings/{listing_id}
```

**Path Parameters:**

| Parameter    | Type    | Description                          |
| ------------ | ------- | ------------------------------------ |
| `listing_id` | integer | The unique identifier of the listing |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/listings/1" \
  -H "Accept: application/json"
```

**Error Response (404):**

```json
{
  "error": "ListingNotFoundError",
  "message": "Property listing not found"
}
```

---

#### Create Listing

Create a new property listing. **Requires authentication.**

```
POST /api/listings/
```

**Headers:**

| Header      | Required | Description                     |
| ----------- | -------- | ------------------------------- |
| `X-API-Key` | Yes      | Your API key for authentication |

**Request Body:**

```json
{
  "address": "42 Oak Street",
  "postcode": "LS1 2AB",
  "price": 350000,
  "property_type": "Semi-Detached",
  "bedrooms": 4
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/listings/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"address": "42 Oak Street", "postcode": "LS1 2AB", "price": 350000, "property_type": "Semi-Detached", "bedrooms": 4}'
```

**Response (201 Created):**

```json
{
  "id": 42,
  "address": "42 Oak Street",
  "postcode": "LS1 2AB",
  "price": 350000,
  "property_type": "Semi-Detached",
  "bedrooms": 4
}
```

---

#### Update Listing

Update an existing property listing. **Requires authentication.**

```
PUT /api/listings/{listing_id}
```

**Headers:**

| Header      | Required | Description                     |
| ----------- | -------- | ------------------------------- |
| `X-API-Key` | Yes      | Your API key for authentication |

**Example Request:**

```bash
curl -X PUT "http://localhost:8000/api/listings/42" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"address": "42 Oak Street", "postcode": "LS1 2AB", "price": 375000, "property_type": "Semi-Detached", "bedrooms": 4}'
```

---

#### Delete Listing

Remove a property listing. **Requires authentication.**

```
DELETE /api/listings/{listing_id}
```

**Headers:**

| Header      | Required | Description                     |
| ----------- | -------- | ------------------------------- |
| `X-API-Key` | Yes      | Your API key for authentication |

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/api/listings/42" \
  -H "X-API-Key: your_api_key_here"
```

**Response:** `204 No Content`

---

### Analytics Endpoints

#### Smart Property Search (LLM-powered)

Leverage generative AI (Google Gemini) to interpret natural language property search queries and translate them into structured database filters.

**Request Body:**

```json
{
"query": "I need a detached family home in LS6 with 3 bedrooms for under £350k"
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/analytics/smart-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "I need a detached family home in LS6 with 3 bedrooms for under £350k"}'
```

**Example Response:**

```json
{
  "ai_interpretation": {
  "max_price": 350000,
  "min_bedrooms": 3,
  "property_types": ["Detached"],
  "postcode_district": "LS6",
  "exact_postcode": null,
  "address_keywords": null
  }
  "results_count": 2,
  "properties": [
    {
      "id": 12,
      "address": "14, Victoria Road",
      "postcode": "LS6 1PF",
      "price": 275000,
      "property_type": "Detached",
      "bedrooms": 3
    }
    // ...more results
  ]
}
```
**How it works:**

*   The endpoint accepts a free-form English query describing property requirements.
    
*   The backend uses Google Gemini (Generative AI) to extract structured search parameters (max price, bedrooms, property type, postcode) from the query.
    
*   The AI is prompted to return strict JSON, which is parsed and used to dynamically build a SQLAlchemy query.
    
*   Results are filtered and returned, along with the AI's interpretation for transparency.
    

**Implementation details:**

*   The Gemini API key must be set as the GEMINI\_API\_KEY environment variable for this feature to work.
    
*   If the key is not set, the endpoint returns a 500 error.
    
*   The prompt engineering ensures robust extraction and strict JSON output from the LLM.

#### Market Summary

Get aggregated statistics grouped by property type, including total listings and average prices.

```
GET /api/analytics/market-summary
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/analytics/market-summary" \
  -H "Accept: application/json"
```

**Example Response:**

```json
[
  {
    "property_type": "Detached",
    "total_listings": 145,
    "average_price": 485000
  },
  {
    "property_type": "Semi-Detached",
    "total_listings": 312,
    "average_price": 275000
  },
  {
    "property_type": "Terraced",
    "total_listings": 428,
    "average_price": 195000
  },
  {
    "property_type": "Flat",
    "total_listings": 203,
    "average_price": 145000
  }
]
```

---

#### Affordability Search

Find properties matching your budget and bedroom requirements.

```
GET /api/analytics/affordability
```

**Query Parameters:**

| Parameter      | Type    | Required        | Description                   |
| -------------- | ------- | --------------- | ----------------------------- |
| `max_price`    | integer | Yes             | Maximum property price in GBP |
| `min_bedrooms` | integer | No (default: 1) | Minimum number of bedrooms    |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/analytics/affordability?max_price=200000&min_bedrooms=2" \
  -H "Accept: application/json"
```

**Example Response:**

Returns up to 10 properties ordered by bedrooms (descending) then price (ascending).

```json
[
  {
    "id": 15,
    "address": "8, Chapel Lane",
    "postcode": "LS12 3CD",
    "price": 185000,
    "property_type": "Terraced",
    "bedrooms": 3
  }
]
```

---

## Data Model

### PropertyListing

| Field           | Type    | Constraints                  | Description                                    |
| --------------- | ------- | ---------------------------- | ---------------------------------------------- |
| `id`            | Integer | Primary Key, Auto-increment  | Unique identifier                              |
| `address`       | String  | Required                     | Street address                                 |
| `postcode`      | String  | Required, UK postcode format | Valid UK postcode                              |
| `price`         | Integer | Required, > 0                | Price in GBP                                   |
| `property_type` | String  | Required                     | Detached, Semi-Detached, Terraced, Flat, Other |
| `bedrooms`      | Integer | Required, >= 0               | Number of bedrooms                             |

**Postcode Validation Pattern:**

```regex
^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$
```

---

## Authentication

Write operations (POST, PUT, DELETE) require API key authentication via the `X-API-Key` header.

**Error Response (403 Forbidden):**

```json
{
  "error": "AuthenticationError",
  "message": "Invalid or missing API Key"
}
```

For local development, set your API key in a `.env` file:

```env
API_KEY=your_secret_api_key_here
```

---

## Local Development

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- Python 3.11+ (optional, for running the import script directly)

**Note:**
*   Azure Monitor / Application Insights integration is not required for local development. The API will run without any Azure-specific environment variables.
    
*   For LLM-powered smart search, set your Gemini API key in a [.env](vscode-file://vscode-app/c:/Users/archi/AppData/Local/Programs/Microsoft VS Code/ce099c1ed2/resources/app/out/vs/code/electron-browser/workbench/workbench.html) file:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ArchieAbr/housing_project_api.git
   cd housing_project_api
   ```

2. **Create environment file:**

   ```bash
   echo "API_KEY=your_secret_key_here" > .env
   echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env
   ```
   *(Note the use of `>>` on the second line so it appends to the file rather than overwriting it).* 

3. **Start the containers:**

   ```bash
   docker-compose up --build
   ```
   **Troubleshooting:** On the very first run, the PostgreSQL database may take a few seconds to initialise. If the API container exits with a database connection error, simply wait 5 seconds and run docker-compose up again.

4. **Access the API:**
   - API Root: http://localhost:8000/
   - Swagger Documentation: http://localhost:8000/docs
   - ReDoc Documentation: http://localhost:8000/redoc

The database will be automatically seeded with Leeds property data on first startup.

### Manual Data Import

If you need to repopulate the database:

```bash
# Install dependencies (if running outside Docker)
pip install psycopg2-binary sqlalchemy

# Run the import script
python import_data.py
```

---

## Running Tests

The test suite is designed as a set of live integration tests that run directly against the deployed Azure server. To execute these tests, you must have a local `.env` file containing the valid `TEST_API_KEY` to authenticate against the live endpoints.

**Warning:** Do not commit your `.env` file to version control.

### 1. Set up the Environment Variables

Load the variables from your `.env` file into your active terminal session.

```bash
export $(grep -v '^#' .env | xargs)
```
### 2. Execute the Test Suite

Once the environment variables are loaded, run the tests using pytest:

```bash
pytest app/test_integration.py -v
```
### Test Coverage Includes:

#### 1. Live endpoint connectivity and health checks

#### 2. API Key authentication and rejection handling

#### 3. Full CRUD lifecycle verification on the production database

#### 4. Data validation (postcode formatting, negative value rejection)

#### 5. Real-time latency checks for the Generative AI (Google Gemini) smart search
---

## Database Migrations

This project uses **Alembic** for database schema management. Migrations run automatically on application startup.

### How It Works

1. Migrations are stored in `app/alembic/versions/`
2. The application checks for pending migrations at startup
3. Schema changes are applied automatically before the API becomes available

### Creating a New Migration

When modifying the database schema:

1. **Update your model** in `app/models.py`

2. **Generate a migration:**

   ```bash
   cd app
   alembic revision --autogenerate -m "Description of changes"
   ```

3. **Review the generated migration** in `app/alembic/versions/`

4. **Commit and deploy** — migrations apply automatically on startup

---

## Deployment

The application is deployed on **Microsoft Azure** using:

- **Azure App Service** (Linux container)
- **Azure Database for PostgreSQL Flexible Server**
- **Azure Container Registry** (for Docker images)

### Environment Variables (Azure)

Configure these in the App Service Configuration:

| Variable       | Description                       |
| -------------- | --------------------------------- |
| `DATABASE_URL` | PostgreSQL connection string      |
| `API_KEY`      | Secret key for API authentication |

### Deployment Flow

1. Push changes to the repository
2. Container image is built and pushed to Azure Container Registry
3. App Service pulls the new image and restarts
4. Alembic migrations run automatically on startup
5. Database is seeded if empty

---

## Data Source

This API is populated with real property transaction data from the **HM Land Registry Price Paid Data**.

- **Source:** [HM Land Registry Open Data](https://www.gov.uk/government/collections/price-paid-data)
- **Licence:** Open Government Licence v3.0
- **Coverage:** Leeds metropolitan area
- **Note:** Bedroom counts are synthetically generated based on property type, as this field is not included in the Land Registry dataset.

---

## Project Structure

```
housing_project_api/
├── app/
│   ├── alembic/              # Database migrations
│   │   └── versions/         # Migration scripts
│   ├── routers/              # API route handlers
│   │   ├── listings.py       # CRUD endpoints
│   │   └── analytics.py      # Analytics endpoints
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic validation schemas
│   ├── db.py                 # Database configuration
│   ├── auth.py               # API key authentication
│   ├── exceptions.py         # Custom exception classes
│   ├── seed.py               # Database seeding logic
│   └── test_main.py          # Test suite
├── docker-compose.yml        # Local development orchestration
├── Dockerfile                # Container image definition
├── import_data.py            # Manual data import script
├── leeds_housing_data.csv    # Source data file
└── README.md
```

---

## Licence

This project was developed for the COMP3011 module at the University of Leeds.

Data sourced from HM Land Registry under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

