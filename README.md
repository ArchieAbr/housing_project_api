# UK Housing Market API (Leeds)

## Project Overview

This project is a RESTful Web Services API developed for the COMP3011 module. It provides a robust, data-driven interface to query and analyse UK housing market transactions, specifically focusing on property data in Leeds. The API is built to demonstrate modern software engineering principles, containerised deployment, and advanced relational database querying.

## Core Features

- **Full CRUD Functionality:** Endpoints to Create, Read, Update, and Delete individual property listings.
- **Market Analytics:** Advanced endpoints providing regional market summaries (average prices by property type) and an affordability calculator.
- **Data Validation:** Strict input validation using Pydantic models.
- **Containerisation:** Fully orchestrated local development environment using Docker Compose.
- **Cloud Ready:** Architected for professional deployment on Azure App Service with a managed PostgreSQL backend.

## Technology Stack

- **Framework:** Python FastAPI
- **Database:** PostgreSQL & SQLAlchemy (ORM)
- **Validation:** Pydantic
- **Containerisation:** Docker & Docker Compose
- **Cloud Deployment:** Azure App Service & Azure Database for PostgreSQL Flexible Server

## Prerequisites

To run this project locally, ensure you have the following installed on your machine:

- Docker Desktop
- Git
- Python 3.11 (strictly for running the local data import script)

## Local Setup and Execution

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/ArchieAbr/housing_project_api.git
   cd housing_project_api
   ```

2. **Start the Docker Containers:**
   Run the following command to build the API image and start both the API and PostgreSQL database containers simultaneously:

   ```bash
   docker-compose up --build
   ```

3. **Access the Application:**
   - The API root health check will be available at: `http://localhost:8000/`
   - Interactive Swagger UI documentation: `http://localhost:8000/docs`

4. **Testing Usage**
   ```bash
   docker-compose exec api pytest app/test_main.py -v
   ```

## Dataset and Data Import

This API is seeded with real-world public data sourced from the **HM Land Registry Price Paid Data** portal.

To populate your local database:

1. Ensure your Docker containers are actively running.
2. Open a separate terminal window in the project root directory.
3. Install the local data parsing dependencies:
   ```bash
   pip install psycopg2-binary sqlalchemy
   ```
4. Execute the import script:
   ```bash
   python import_data.py
   ```
   _Note: The import script dynamically mocks "bedroom" counts to ensure full schema compatibility, as this specific metric is absent from the official Land Registry dataset._

## Acknowledgements & Academic Integrity

- **Data Source:** HM Land Registry Price Paid Data (Licensed under the Open Government Licence v3.0).
- **Generative AI:** This project was developed in compliance with the COMP3011 'GREEN' GenAI policy. AI tools were utilised for architectural ideation, debugging, and data processing.

---

## Database Migrations with Alembic

This project uses **Alembic** for database schema management. Migrations are version-controlled and run automatically on deployment.

### How It Works

1. **Automatic Migrations:** When the app starts (locally or on Azure), it automatically runs any pending migrations
2. **Version Tracking:** Each migration is stored in `app/alembic/versions/` and tracked in the database
3. **No Duplicates:** Alembic tracks which migrations have been applied, so they only run once

### Making Schema Changes

When you need to modify the database schema (add tables, columns, etc.):

#### Step 1: Modify Your Model

Edit `app/models.py` with your changes:

```python
class PropertyListing(Base):
    __tablename__ = "property_listings"
    # ... existing columns ...
    energy_rating = Column(String, nullable=True)  # NEW COLUMN
```

#### Step 2: Generate Migration

Navigate to the `app/` directory and run:

```bash
cd app
alembic revision --autogenerate -m "Add energy_rating column"
```

This creates a new migration file in `app/alembic/versions/`.

#### Step 3: Review the Migration

Open the generated file and verify the `upgrade()` and `downgrade()` functions are correct.

#### Step 4: Test Locally

```bash
# Apply migration to local Docker database
alembic upgrade head
```

#### Step 5: Deploy

Commit and push your changes:

```bash
git add -A
git commit -m "Add energy_rating column"
git push
```

The migration will run automatically when the Azure app restarts.

### Useful Alembic Commands

Run these from the `app/` directory:

| Command                                        | Description                    |
| ---------------------------------------------- | ------------------------------ |
| `alembic current`                              | Show current migration version |
| `alembic history`                              | Show migration history         |
| `alembic upgrade head`                         | Apply all pending migrations   |
| `alembic downgrade -1`                         | Rollback last migration        |
| `alembic revision --autogenerate -m "message"` | Generate new migration         |

### Environment Setup for Local Development

When running Alembic commands locally, ensure your `DATABASE_URL` environment variable is set:

```bash
# For local Docker database
export DATABASE_URL="postgresql://user:password@localhost:5432/housing_db"

# Or set it inline
DATABASE_URL="postgresql://user:password@localhost:5432/housing_db" alembic upgrade head
```

### Migration Best Practices

1. **Always review auto-generated migrations** - Alembic may not detect all changes perfectly
2. **Test migrations locally** before deploying to production
3. **Keep migrations small** - One logical change per migration
4. **Never edit migrations** that have been deployed to production
5. **Write reversible migrations** - Always implement `downgrade()` functions
