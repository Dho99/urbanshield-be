You are a senior backend architect and data platform engineer.

Build the backend architecture and implementation plan for:

UrbanShield AI

Project:

"Explainable Geospatial Intelligence System for Urban Flood Risk Prediction and Mitigation Prioritization"


The backend must support:

- authentication
- user management
- geospatial risk visualization
- flood risk prediction inference
- explainable AI result
- mitigation recommendation
- dataset management
- analytics dashboard


This is not a generic CRUD application.

The backend is the core decision-support API layer between:

Frontend Dashboard

        ↓

Backend Services

        ↓

Machine Learning Model

        ↓

Geospatial Database


==================================================
TECH STACK REQUIREMENT
==================================================


Use:


Backend Framework:

FastAPI (Python)


Database:

PostgreSQL

Extension:

PostGIS


ORM:

SQLAlchemy


Migration:

Alembic


Authentication:

Better Auth compatible

Use:

JWT/session based authentication


Validation:

Pydantic


ML Serving:

Python model service

Support:

- XGBoost
- LightGBM
- Scikit-learn


Documentation:

OpenAPI / Swagger


Deployment ready:

Docker


==================================================
SYSTEM ROLE
==================================================


UrbanShield backend responsibilities:


1. Authentication Service

Manage:

- user registration
- login
- session validation
- role authorization


User roles:


ADMIN

Can:

- manage users
- manage datasets
- monitor system


ANALYST

Can:

- analyze risk
- access prediction
- view explainability


VIEWER

Can:

- view dashboard
- view public risk information



==================================================
2. GEO SPATIAL DATA SERVICE
==================================================


Purpose:

Provide map and geographic information.


Manage:


Administrative area:

- province
- city
- district
- polygon boundary


Infrastructure:


- rivers
- roads
- facilities


Risk layers:


- flood risk polygon
- risk score


Required API:


GET /api/v1/areas

Return monitored areas.


GET /api/v1/areas/{id}


Return:

- geometry
- metadata
- risk summary



GET /api/v1/map/risk-layer


Return:

GeoJSON FeatureCollection


Example:


{
"type":"FeatureCollection",
"features":[]
}


==================================================
3. FLOOD RISK PREDICTION SERVICE
==================================================


Purpose:

Serve machine learning inference.


Input:


district_id


or:


feature values:



{
rainfall:250,
elevation:600,
population_density:15000,
drainage_density:0.3
}



Process:


1.
Validate input


2.
Feature preprocessing


3.
Run ML model


4.
Generate prediction


5.
Generate SHAP explanation



Output:


{
risk_level:"HIGH",

risk_score:82,

confidence:0.87,

factors:[
{
feature:"rainfall",
contribution:35
}
]

}


API:


POST /api/v1/predictions


==================================================
4. EXPLAINABLE AI SERVICE
==================================================


Purpose:


Explain why model predicts a certain risk.


Support:


SHAP output.


API:


GET /api/v1/predictions/{id}/explanation



Response:


{
main_factors:[
{
feature:"drainage_density",
impact:"positive",
value:0.25
}
]
}


==================================================
5. MITIGATION RECOMMENDATION SERVICE
==================================================


Purpose:

Convert risk information into actionable recommendation.



Input:


- risk score
- contributing factors
- area condition



Output:


{
priority:"HIGH",

recommendations:[

{
action:"Improve drainage capacity",

reason:"Low drainage density"

}

]

}



API:


GET /api/v1/recommendations/{area_id}



==================================================
6. DATA MANAGEMENT SERVICE
==================================================


Manage:


Dataset:


- BNPB
- BMKG
- BPS
- OSM
- DEM


Provide:


GET /api/v1/datasets


Return:

- dataset name
- source
- last update
- completeness



==================================================
DATABASE DESIGN
==================================================


Design ERD.


Minimum tables:


users

roles

areas

area_boundaries

risk_predictions

prediction_factors

recommendations

datasets

osm_features

weather_features

population_features


Use PostGIS geometry columns.


==================================================
API DOCUMENTATION REQUIREMENT
==================================================


Generate complete API documentation:


For every endpoint provide:


- method
- URL
- authentication requirement
- request body
- query parameters
- response schema
- error response


Format:


## POST /api/v1/predictions


Description:

Run flood risk prediction.


Authorization:

Bearer token


Request:


Response:


Errors:



==================================================
NON FUNCTIONAL REQUIREMENTS
==================================================


Implement:


Security:

- JWT validation
- role based access
- input validation


Performance:

- caching risk layer
- pagination


Maintainability:

- modular service architecture


Logging:

- API request logs
- model inference logs


==================================================
PROJECT STRUCTURE
==================================================


Expected:


backend/

├── app/

│
├── api/

├── core/

├── models/

├── schemas/

├── services/

│   ├── auth_service.py
│   ├── prediction_service.py
│   ├── map_service.py
│   └── recommendation_service.py

├── ml/

│   ├── model_loader.py
│   ├── predictor.py
│   └── explainer.py

├── database/

├── migrations/

└── main.py



==================================================
IMPLEMENTATION STRATEGY
==================================================


Implement incrementally:


Phase 1:

Project setup

Database

Authentication


Phase 2:

Geospatial service


Phase 3:

Prediction inference API


Phase 4:

SHAP explanation


Phase 5:

Recommendation service


Phase 6:

API documentation


Do not create fake business logic.

Use clear interfaces so ML model can be replaced later.


==================================================
FINAL OUTPUT
==================================================


Produce:


1.
Backend PRD


2.
System architecture


3.
Database schema


4.
API specification


5.
Implementation roadmap


6.
Initial backend implementation