from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np
import shap


app = FastAPI(
    title="UrbanShield AI Inference API"
)


model = pickle.load(
    open("model/model.pkl", "rb")
)

explainer = pickle.load(
    open("model/shap_explainer.pkl", "rb")
)


FEATURES = [
    "rainfall_mm",
    "elevation_mean",
    "slope_mean",
    "basin_depression_index",
    "river_density_km",
    "water_ratio",
    "population_density",
    "building_density",
    "road_density",
    "facility_density",
    "impervious_ratio",
    "drainage_density_km",
    "effective_drainage_capacity",
    "green_ratio"
]


class PredictionInput(BaseModel):

    features: list[float]


@app.get("/")
def home():
    return {
        "status": "UrbanShield AI online"
    }


@app.post("/predict")
def predict(data: PredictionInput):

    x = np.array(
        data.features
    ).reshape(1, -1)

    score = float(
        model.predict(x)[0]
    )

    shap_values = explainer.shap_values(x)

    factors = []

    for name, value in zip(
        FEATURES,
        shap_values[0]
    ):

        factors.append(
            {
                "feature": name,
                "impact": float(value)
            }
        )

    if score < 40:
        level = "Low"

    elif score < 70:
        level = "Medium"

    else:
        level = "High"

    return {

        "risk_score": round(score, 2),

        "risk_level": level,

        "shap": factors

    }
