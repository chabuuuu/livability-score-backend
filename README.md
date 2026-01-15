# Geospatial Real Estate Analytics & Recommendation Platform: The Livability Engine

This repository contains the **Polyglot Microservices Backend** for a next-generation real estate research platform. Moving beyond traditional search engines that rely solely on static attributes (price, area), this system introduces a **Livability Score Engine** to quantify the quality of life at any given coordinate using geospatial intelligence and real-time social indicators.

## The Core Vision
The primary research goal is to bridge the information gap between real estate pricing and environmental context. By integrating **GIS (Geographic Information Systems)**, **Machine Learning**, and **LLMs**, the platform transforms raw urban data into actionable insights, allowing users to find homes that truly match their lifestyle preferences.

---

## 🚀 Research & Technical Innovations

### 1. The Multi-Criteria Livability Framework
Our research defines "Livability" through two distinct dimensions:
*   **Static Indicators (Environmental Baseline):** Calculated using PostGIS spatial queries (`ST_DWithin`) across seven categories: Healthcare, Education, Shopping, Transportation, Environment (Green Space), Entertainment, and Safety. 
    *   *Methodology:* Employs **Distance Decay** functions for proximity-based services and **Saturation functions** for density-based amenities.
*   **Dynamic Social Indicators (Real-time Risk/Potential):** A novel approach that scrapes real-time news (floods, accidents, urban planning) and uses **LLM** to perform sentiment analysis and spatial impact scoring.

### 2. Explainable AI (XAI) in Valuation
The system doesn't just predict prices; it explains them. Using a **Hedonic Pricing Model** implemented via **LightGBM**, we integrate Livability Scores as key features. 
*   **SHAP (SHapley Additive exPlanations):** We utilize SHAP to quantify the impact of environmental factors on property value, proving scientifically that "Environment" and "Transport" scores significantly drive market prices.

### 3. Adaptive Data Strategy (Grid-based Gap Analysis)
To optimize data costs and coverage, the system employs a unique ETL strategy:
*   **OSM-Google Hybrid:** The system partitions the map into a grid. It primarily harvests data from **OpenStreetMap** and triggers targeted **Google Places API** scans only in "data-deficient" cells identified by our Gap Analysis algorithm.

### 4. Real-time Geospatial Intelligence
Leveraging **Golang** and **Redis Geo**, the platform implements high-concurrency background location tracking to push "Context-Aware" notifications when a user enters a high-livability zone matching their profile.

---

## 🏗 Polyglot Microservices Architecture

The backend is engineered for scalability and specialized performance, utilizing the best language for each task:

| Service | Technology | Primary Responsibility |
| :--- | :--- | :--- |
| **User Service** | Java Spring Boot | Secure identity management, RBAC, and preference profiles. |
| **Property Service** | Java Spring Boot | High-reliability CRUD operations and PostGIS-backed spatial search. |
| **Recommendation Service** | Python (FastAPI/Flask) | Price prediction (LightGBM), SHAP analysis, and LLM-powered Chatbot insights. |
| **Location Service** | Golang (Gin) | Real-time background GPS tracking and Redis Geo-spatial matching. |
| **Special Indicator Service** | Python (Scrapy/Gemini) | Autonomous news crawling and AI-driven social impact scoring. |
| **Amenity Collector** | Python (Pandas/GeoPandas) | Automated ETL pipelines for urban infrastructure enrichment. |
| **Media Service** | Node.js (TypeScript) | Efficient handling of high-volume image/video uploads to **MinIO**. |

### Explainable Chatbot
The system integrates a **Context-Aware Chatbot** that doesn't just provide numbers. It pulls surrounding amenity data and news impacts to explain: *"This property has a high safety score because it is within 500m of a police station, but the transport score is lower due to recent flood reports in this sector"*.

---
**Disclaimer:** This project is a research-focused implementation exploring the intersection of Urban Science and Artificial Intelligence. All pricing predictions and livability scores are based on the integrated mathematical models and available geospatial data.
