import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI
from pydantic import BaseModel
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import f1_score, confusion_matrix

app = FastAPI(title="API Modelos ML - Autolavado Expréss La Estancia")

# Generación de serie histórica calibrada para entrenamiento rápido al arrancar
rng = np.random.default_rng(42)
fechas = pd.date_range(end=datetime.today(), periods=180, freq="D")
base = 45 + np.arange(180) * 0.03 + np.where(fechas.dayofweek >= 4, 15, 0) + np.where(fechas.day.isin([15, 30, 1]), 12, 0)
demanda = np.maximum(10, rng.poisson(base)).astype(float)
serie_diaria = pd.Series(demanda, index=fechas)

# Entrenar ARIMA(2,1,2)
modelo_arima = ARIMA(serie_diaria, order=(2, 1, 2)).fit()

# Entrenar Clasificadores (Básico=0 vs Detallado=1)
X_train = rng.normal(size=(500, 3)) # [dia_semana, hora, es_quincena]
y_train = (X_train[:, 0] + X_train[:, 2] > 0.3).astype(int)
modelos_clf = {
    "NaiveBayes": GaussianNB().fit(X_train, y_train),
    "KNN": KNeighborsClassifier(n_neighbors=5).fit(X_train, y_train),
    "RandomForest": RandomForestClassifier(n_estimators=50, random_state=42).fit(X_train, y_train)
}

class SolicitudClasificacion(BaseModel):
    dia_semana: int
    hora: int
    es_quincena: int

@app.get("/health")
def health():
    return {"status": "ok", "aic_arima": round(modelo_arima.aic, 2)}

@app.get("/pronostico")
def pronostico(dias: int = 7):
    dias = max(7, min(30, dias))
    pred = modelo_arima.get_forecast(steps=dias)
    media = pred.predicted_mean
    conf = pred.conf_int(alpha=0.05)
    
    resultados = []
    for i in range(dias):
        fecha_futura = (datetime.today() + timedelta(days=i+1)).strftime("%Y-%m-%d")
        resultados.append({
            "fecha": fecha_futura,
            "autos_estimados": round(float(media.iloc[i]), 1),
            "limite_inferior": max(0, round(float(conf.iloc[i, 0]), 1)),
            "limite_superior": round(float(conf.iloc[i, 1]), 1)
        })
    return {"modelo": "ARIMA(2,1,2)", "aic": round(modelo_arima.aic, 2), "pronostico": resultados}

@app.post("/clasificar")
def clasificar(datos: SolicitudClasificacion):
    X = np.array([[datos.dia_semana, datos.hora, datos.es_quincena]])
    pred_rf = int(modelos_clf["RandomForest"].predict(X)[0])
    prob_rf = float(modelos_clf["RandomForest"].predict_proba(X)[0][pred_rf])
    
    y_pred_eval = modelos_clf["RandomForest"].predict(X_train)
    return {
        "prediccion": "Servicio Detallado" if pred_rf == 1 else "Servicio Básico",
        "probabilidad": round(prob_rf, 3),
        "metricas_validacion": {
            "f1_score": round(float(f1_score(y_train, y_pred_eval)), 3),
            "matriz_confusion": confusion_matrix(y_train, y_pred_eval).tolist()
        }
    }
