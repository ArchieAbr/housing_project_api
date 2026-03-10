# UK Housing Market API (Leeds)

## Project Overview
This project is a RESTful Web Services API developed for the COMP3011 module. It provides a robust, data-driven interface to query and analyse UK housing market transactions, specifically focusing on property data in Leeds. The API is built to demonstrate modern software engineering principles, containerised deployment, and advanced relational database querying.

## Core Features
* **Full CRUD Functionality:** Endpoints to Create, Read, Update, and Delete individual property listings.
* **Market Analytics:** Advanced endpoints providing regional market summaries (average prices by property type) and an affordability calculator.
* **Data Validation:** Strict input validation using Pydantic models.
* **Containerisation:** Fully orchestrated local development environment using Docker Compose.
* **Cloud Ready:** Architected for professional deployment on Azure App Service with a managed PostgreSQL backend.

## Technology Stack
* **Framework:** Python FastAPI
* **Database:** PostgreSQL & SQLAlchemy (ORM)
* **Validation:** Pydantic
* **Containerisation:** Docker & Docker Compose
* **Cloud Deployment:** Azure App Service & Azure Database for PostgreSQL Flexible Server

## Prerequisites
To run this project locally, ensure you have the following installed on your machine:
* Docker Desktop
* Git
* Python 3.11 (strictly for running the local data import script)

## Local Setup and Execution
1. **Clone the Repository:**
   ```bash
   git clone <your-github-repo-url>
   cd housing_project_api
   ```

2. **Start the Docker Containers:**
   Run the following command to build the API image and start both the API and PostgreSQL database containers simultaneously:
   ```bash
   docker-compose up --build
   ```

3. **Access the Application:**
   * The API root health check will be available at: `http://localhost:8000/`
   * Interactive Swagger UI documentation: `http://localhost:8000/docs`

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
*Note: The import script dynamically mocks "bedroom" counts to ensure full schema compatibility, as this specific metric is absent from the official Land Registry dataset.*


## Acknowledgements & Academic Integrity
* **Data Source:** HM Land Registry Price Paid Data (Licensed under the Open Government Licence v3.0).
* **Generative AI:** This project was developed in compliance with the COMP3011 'GREEN' GenAI policy. AI tools were utilised for architectural ideation, debugging, and data processing.