# Real Estate Intelligence Platform: An AI-Driven Approach to Valuation and Livability Assessment

## 📖 Abstract

This repository contains the backend source code for a comprehensive **Real Estate Intelligence Platform**, developed as a graduation thesis. The system addresses the opacity and information asymmetry in the urban real estate market by integrating **Automated Valuation Models (AVM)** with **Geospatial Analysis** and **Generative AI**.

Unlike traditional property listing platforms, this system introduces a novel **"Livability Score"** framework, calculated via a hybrid pipeline of OpenStreetMap (OSM) and Google Places API data. It features an explainable pricing engine powered by **LightGBM** and **SHAP**, a retrieval-augmented generation (RAG) chatbot for contextual insights, and a dynamic news analysis module that quantifies real-time urban risks (e.g., flooding, accidents) using Large Language Models (LLMs).

## 🚀 Key Features

### 1. Advanced Automated Valuation Model (AVM)

* **Algorithm:** Utilizes **LightGBM** (Light Gradient Boosting Machine) optimized via `RandomizedSearchCV`.
* **Data Processing:** Implements robust preprocessing pipelines including **Log-Transformation** for skewed price distributions and **Robust Scaling** for outlier mitigation.
* **Performance:** Achieves an  of **~0.71** with a model footprint of only **16MB** (compared to 580MB for Random Forest), optimizing container startup time and memory usage.
* **Explainable AI (XAI):** Integrated **SHAP (SHapley Additive exPlanations)** values to provide transparency on feature importance (e.g., how much location vs. area contributes to the price).

### 2. Geospatial Livability Scoring Engine

* **Multi-Source Data Pipeline:** A hybrid ETL process aggregating Points of Interest (POIs) from **OpenStreetMap** (base layer) and **Google Places API** (gap filling for data-sparse districts).
* **Spatial deduplication:** Algorithms to merge and deduplicate entities based on spatial proximity and Levenshtein string distance.
* **Scoring Logic:** Computes a composite index based on 7 dimensions: *Healthcare, Education, Shopping, Transportation, Environment, Entertainment, and Public Safety*. Utilizes **Distance Decay** and **Density Saturation** functions to model real-world urban accessibility.

### 3. Dynamic Urban Intelligence (News Crawler & Analysis)

* **Real-time Monitoring:** Automated crawlers (using `DuckDuckGo` & `Newspaper3k`) scan for hyperlocal news regarding **Flooding**, **Traffic Accidents**, and **Infrastructure Projects**.
* **Semantic Analysis:** Leverages **Google Gemini** to validate relevance, extract sentiment, and quantify impact scores (1-10).
* **Cross-Database Propagation:** Propagates aggregated district-level risk scores to individual properties via PostGIS spatial queries, ensuring listings reflect the latest environmental reality.

### 4. Hybrid Recommendation System

* **Architecture:** A tiered recommendation engine combining **Spatial Filtering** (PostGIS) and **Content-Based Filtering**.
* **Preference Matching:** A custom algorithm that matches properties not just by price/area, but by the user's specific "Livability Profile" (e.g., prioritizing *Education* over *Nightlife*).
* **Cold-Start Handling:** Fallback mechanisms utilizing popularity metrics and spatial proximity for new users.

### 5. Context-Aware AI Assistant

* **RAG Architecture:** A chatbot capable of answering specific questions about a property by retrieving real-time context (Livability scores, nearby amenities, recent news).
* **Resilience:** Implements a **Round-Robin API Key Rotation** and **Model Fallback Pool** strategy to handle high concurrency and API rate limits.
* **Streaming Response:** Full support for Server-Sent Events (SSE) for low-latency conversational experiences.


*Note: Benchmarks conducted on a dataset of 133,200 properties in Ho Chi Minh City.*

## 🤝 Contribution

This project was developed for academic research purposes. Contributions, issues, and feature requests are welcome.

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Author: chabuuuu
