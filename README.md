Here is a comprehensive, high-level `README.md` written entirely in professional English. It is structured to serve as technical documentation for developers and a defense of your methodology for your thesis advisors.

I have explicitly integrated the solutions to your teacher's feedback into a section called **"Scientific Methodology & Data Integrity"**.

---

# Smart Real Estate Platform: Backend & Livability Engine

## 📖 Executive Summary

This repository hosts the backend microservices ecosystem for the **Smart Real Estate Platform**, a graduation thesis project designed to revolutionize property searching.

Unlike traditional platforms that focus solely on price and area, this system introduces a proprietary **"Livability Score Engine."** This engine aggregates multi-dimensional geospatial data to objectively quantify the quality of life for any given location, aiding users in making informed decisions based on safety, convenience, education, and future potential.

---

## 🔬 Scientific Methodology & Data Integrity

To ensure the system's reliability and academic rigor, we address core challenges regarding data sourcing, weighting logic, and user-generated content quality.

### 1\. The Factor Framework (Urban Planning Standards)

The components of the Livability Score are not arbitrary. They are derived from established urban planning frameworks such as the **"15-Minute City" concept** and the **OECD Better Life Index**.

- **Core Pillars:** Safety, Healthcare, Education, Mobility (Transportation), Environment, and Convenience.

### 2\. Weight Determination (The Hedonic Pricing Model)

We moved beyond subjective manual weighting. The system employs a **Data-Driven Approach** using Machine Learning:

- **Model:** We utilize **XGBoost** to perform regression analysis on property prices against surrounding amenities (Hedonic Pricing).
- **Explainability:** Using **SHAP (SHapley Additive exPlanations)**, we extract the "Feature Importance" of each amenity category.
- **Logic:** If the model detects that "Proximity to Parks" significantly increases property value in a specific district, the "Environment" factor automatically receives a higher weight for that zone.

### 3\. Data Quality Assurance (Anti-Fraud & Price Validation)

Since the platform allows user-generated listings, we implement a **Statistical Anomaly Detection** pipeline to prevent "virtual prices" (fake pricing) from corrupting the training dataset:

1.  **Ground Truth Establishment:** We maintain a `market_price_trends` table derived from thousands of verified crawled listings (Mogi.vn).
2.  **Z-Score Analysis:** When a user submits a property, the system calculates the Z-Score of their requested price against the local average.
3.  **Outlier Filtering:** Listings with prices deviating significantly (e.g., \> ±2 Standard Deviations) are flagged as "Unverified Outliers" and are **excluded** from the model retraining pipeline to maintain data purity.

---

## 🏗 System Architecture

The system follows a **Microservices Architecture** to ensure scalability and technology agnosticism.

### Service Breakdown

| Service Name         | Tech Stack         | Responsibility                                                                            |
| :------------------- | :----------------- | :---------------------------------------------------------------------------------------- |
| **User Service**     | Java (Spring Boot) | Authentication (JWT), User Profiles, Role Management.                                     |
| **Property Service** | Node.js / Java     | Core Property CRUD, Spatial Search (PostGIS), Image Management.                           |
| **Scoring Engine**   | Python (FastAPI)   | **[CORE]** Calculates Livability Scores, runs ML inference, processes geospatial queries. |
| **Data Ingestion**   | Python (Scrapy)    | ETL Pipeline. Crawls Mogi.vn, scrapes news, and integrates with Gemini API.               |

### Infrastructure Components

- **Database:** PostgreSQL with **PostGIS** extension (Crucial for `GEOMETRY` data types and `ST_Distance` calculations).
- **Caching:** Redis (Caches calculated Livability Scores to reduce database load).
- **AI Service:** Google Gemini API (For Natural Language Processing of urban planning news).
- **Orchestration:** Docker & Docker Compose (Local), Kubernetes (Production ready).

---

## 💡 Key Technical Features

### 1\. Precision Geolocation Strategy

Instead of relying on inaccurate text-to-address Geocoding APIs, the Ingestion Service utilizes a custom Spider:

- **Technique:** It parses the `<iframe>` source of the embedded Google Maps within Mogi.vn listing pages.
- **Result:** Extracts exact `(latitude, longitude)` coordinates, ensuring 100% location accuracy for the scoring engine.

### 2\. Future Potential Analysis (GenAI Integration)

The system predicts future value increases by analyzing infrastructure projects:

- **Input:** Unstructured news articles (e.g., "Metro Line 1 completion delayed to 2024").
- **Process:** **Google Gemini API** processes the text to extract structured entities: `{ "project": "Metro Line 1", "type": "Transport", "status": "Ongoing", "location": [lat, long] }`.
- **Output:** Stored in `future_amenities` table to add "Potential Bonus Points" to the Livability Score.

---

## 🗄 Database Schema Design

The schema is optimized for spatial querying. Key tables include:

```sql
-- Core Property Table
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    price DECIMAL(15, 2),
    area FLOAT,
    location GEOMETRY(POINT, 4326), -- PostGIS Spatial Data
    source_url TEXT UNIQUE,
    verified BOOLEAN DEFAULT FALSE,
    ...
);

-- Market Trends for Anomaly Detection
CREATE TABLE market_price_trends (
    district_id INT,
    avg_price_per_sqm DECIMAL,
    std_dev_price DECIMAL, -- Standard Deviation for outlier detection
    last_updated TIMESTAMP
);

-- Future Infrastructure
CREATE TABLE future_amenities (
    id SERIAL PRIMARY KEY,
    project_name TEXT,
    location GEOMETRY(POINT, 4326),
    completion_year INT,
    impact_score FLOAT
);
```

---

## 🚀 Installation & Setup

### Prerequisites

- Docker Desktop & Docker Compose
- Python 3.10+ / Java JDK 17+ / Node.js 18+
- API Keys: Google Gemini API, Mapbox (for frontend visualization).

### Step-by-Step Guide

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/your-username/smart-real-estate-backend.git
    cd smart-real-estate-backend
    ```

2.  **Environment Variables**
    Create a `.env` file in the root directory:

    ```env
    # Database
    POSTGRES_USER=admin
    POSTGRES_PASSWORD=secure_password
    POSTGRES_DB=real_estate_db

    # AI Services
    GEMINI_API_KEY=your_google_gemini_key

    # Scoring Config
    MAX_SEARCH_RADIUS_KM=2.0
    ```

3.  **Start Services via Docker**

    ```bash
    docker-compose up --build -d
    ```

4.  **Database Migration & Seeding**
    Initialize PostGIS extension and seed basic data:

    ```bash
    docker exec -it postgres_container psql -U admin -d real_estate_db -f /docker-entrypoint-initdb.d/init_postgis.sql
    ```

### API Documentation

Once running, access the interactive Swagger documentation:

- **Scoring Service:** `http://localhost:8000/docs`
- **User Service:** `http://localhost:8080/swagger-ui.html`

---

## 🧪 Data Pipeline Workflow

1.  **Ingestion:** The Scrapy spider triggers daily. It crawls listings and extracts coordinates.
2.  **Cleaning:** Data enters the `properties` table. Invalid coordinates or duplicate URLs are rejected.
3.  **NLP Analysis:** The News Spider scrapes urban planning articles. Gemini API extracts project data and inserts it into `future_amenities`.
4.  **Scoring Request:**
    - Frontend sends coordinates `(x, y)`.
    - Backend queries PostGIS for all POIs within 2km.
    - Backend queries `future_amenities` for upcoming projects.
    - Model applies weights and returns the final **Livability Score (0-100)**.

---

## 🤝 Contributing & License

This project is open for educational purposes and research contributions.

- **License:** MIT License.
- **Contact:** [Your Name/Email] - Backend Team Lead.

---
