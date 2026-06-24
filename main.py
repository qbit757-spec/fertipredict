from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import shap
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

#Para consumir la API
app = FastAPI(title="FertiPredict ML API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # o ["null"] si abres el HTML como archivo local
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FertiPredict ML API is running"}

# Cargar el modelo entrenado al iniciar la API
model = joblib.load("model_ensemble.pkl")

# Cargar el modelo de XAI
background = joblib.load("background_data.pkl")
if hasattr(background, 'iloc'):
    background = background.iloc[:20]
else:
    background = background[:20]

class PredictionInput(BaseModel):
    Edad_Masculino: int
    IMC_Masculino: float
    Concentracion_Esperma: float
    Motilidad_Espermatica: float
    Morfologia_Espermatica: float
    Varicocele: int
    Exposicion_Toxicos_Calor_Masculino: int
    Fumador_Masculino: int
    Consumo_Alcohol_Masculino: int
    Nivel_Ejercicio_Masculino: int
    Tipo_Alimentacion_Masculino: int
    Historial_Familiar_Infertilidad_Masculino: int

    Edad_Femenino: int
    IMC_Femenino: float
    Ciclo_Menstrual: int
    PCOS: int
    Endometriosis: int
    Hormona_AMH: float
    Hormona_FSH: float
    Obstruccion_Tubaria: int
    Abortos_Previos: int
    Fumador_Femenino: int
    Consumo_Alcohol_Femenino: int
    Nivel_Ejercicio_Femenino: int
    Tipo_Alimentacion_Femenino: int
    Historial_Familiar_Infertilidad_Femenino: int


@app.post("/predict")
def predict(data: PredictionInput):
    # Construir el DataFrame en el mismo orden de columnas que usó el modelo al entrenar
    input_data = pd.DataFrame([{
        "Edad_Masculino": data.Edad_Masculino,
        "IMC_Masculino": data.IMC_Masculino,
        "Concentracion_Esperma": data.Concentracion_Esperma,
        "Motilidad_Espermatica": data.Motilidad_Espermatica,
        "Morfologia_Espermatica": data.Morfologia_Espermatica,
        "Varicocele": data.Varicocele,
        "Exposicion_Toxicos_Calor_Masculino": data.Exposicion_Toxicos_Calor_Masculino,
        "Fumador_Masculino": data.Fumador_Masculino,
        "Consumo_Alcohol_Masculino": data.Consumo_Alcohol_Masculino,
        "Nivel_Ejercicio_Masculino": data.Nivel_Ejercicio_Masculino,
        "Tipo_Alimentacion_Masculino": data.Tipo_Alimentacion_Masculino,

        "Edad_Femenino": data.Edad_Femenino,
        "IMC_Femenino": data.IMC_Femenino,
        "Ciclo_Menstrual": data.Ciclo_Menstrual,
        "PCOS": data.PCOS,
        "Endometriosis": data.Endometriosis,
        "Hormona Antimulleriana (amh)": data.Hormona_AMH,
        "hormona foliculoestimulante (fsh)": data.Hormona_FSH,
        "Obstruccion_Tubaria": data.Obstruccion_Tubaria,
        "Abortos_Previos": data.Abortos_Previos,
        "Fumador_Femenino": data.Fumador_Femenino,
        "Consumo_Alcohol_Femenino": data.Consumo_Alcohol_Femenino,
        "Nivel_Ejercicio_Femenino": data.Nivel_Ejercicio_Femenino,
        "Tipo_Alimentacion_Femenino": data.Tipo_Alimentacion_Femenino,
        
        "Historial_Familiar_Infertilidad_Masculino": data.Historial_Familiar_Infertilidad_Masculino,
        "Historial_Familiar_Infertilidad_Femenino": data.Historial_Familiar_Infertilidad_Femenino
    }])

    prediction = model.predict(input_data)[0]
    probabilities = model.predict_proba(input_data)[0]
    
    predicted_class = int(prediction)
    risk_labels = {0: "LOW", 1: "MODERATE", 2: "HIGH"}
    risk_level = risk_labels[int(prediction)]
    probability = round(float(probabilities[2]) * 100, 2)

    #SHAP Local
    base_models = model.estimators_
    shap_explainer = shap.TreeExplainer(base_models[0])
    
    sv = shap_explainer.shap_values(input_data)

    shap_for_class = sv[0, :, predicted_class]

    feature_names = list(input_data.columns)
    explanation = {
        feature_names[i]: round(float(shap_for_class[i]), 4)
        for i in range(len(feature_names))
    }

    #shap_arrays = []
    #for m in base_models:
    #    try:
    #        exp = shap.TreeExplainer(m)
    #        sv = exp.shap_values(input_data)
    #        if isinstance(sv, list):
    #            shap_arrays.append(sv[predicted_class][0])
    #        else:
    #            shap_arrays.append(sv[0])
    #    except Exception as e:
    #        print(f"SHAP falló para {m}: {e}")
    #        continue
    #
    #shap_for_class = np.mean(shap_arrays, axis=0)
    #feature_names = list(input_data.columns)
    #explanation = {
    #    feature_names[i]: round(float(shap_for_class[i]), 4)
    #    for i in range(len(feature_names))
    #}

    return {
        "riskLevel": risk_level,
        "probability": probability,
        "explanation": explanation
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

#Comandos para levantar la FastAPI
#venv\Scripts\activate
#uvicorn main:app --reload --port 8000