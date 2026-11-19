import numpy as np
import pandas as pd
import sqlite3
from scipy.fft import fft, fftfreq
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from sklearn.linear_model import LinearRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, confusion_matrix, classification_report, f1_score

# Cargar datos limpios desde la base local (o generar respaldo si no existe)
try:
    conn = sqlite3.connect("services/tablero/autolavado.db")
    df = pd.read_sql_query("SELECT * FROM ventas", conn)
    conn.close()
    print(f"Datos cargados desde SQLite: {len(df):,} registros.")
except Exception:
    rng = np.random.default_rng(42)
    fechas = pd.date_range("2020-01-01", "2025-12-31", freq="D")
    n = len(fechas)
    demanda = 45 + np.arange(n)*0.005 + 12*np.sin(2*np.pi*np.arange(n)/7) + 10*np.sin(2*np.pi*np.arange(n)/15) + rng.normal(0, 5, n)
    df = pd.DataFrame({"fecha": fechas, "autos": np.maximum(10, demanda.astype(int))})
    print("Usando serie diaria agregada de respaldo.")

# Agregar ventas diarias
col_fecha = [c for c in df.columns if "fecha" in c.lower()][0]
df[col_fecha] = pd.to_datetime(df[col_fecha])
diario = df.groupby(col_fecha).size().reset_index(name="autos") if "autos" not in df.columns else df[[col_fecha, "autos"]]
diario = diario.set_index(col_fecha).asfreq("D").fillna(method="ffill")

print("\n=== E1: ANÁLISIS ESPECTRAL (FFT) ===")
y = diario["autos"].values - np.mean(diario["autos"].values)
N = len(y)
yf = np.abs(fft(y))[:N//2]
xf = fftfreq(N, 1)[:N//2]
top_idx = np.argsort(yf)[::-1][1:6]
for idx in top_idx:
    if xf[idx] > 0:
        periodo_dias = 1.0 / xf[idx]
        print(f"Frecuencia: {xf[idx]:.4f} ciclos/día -> Periodo dominante: {periodo_dias:.1f} días (Amplitud: {yf[idx]:.1f})")

print("\n=== E2: SERIE DE TIEMPO (ADF, ACF, PACF) Y REGRESIÓN A MANO CON NUMPY ===")
adf_res = adfuller(diario["autos"])
print(f"Estadístico ADF: {adf_res[0]:.4f} | p-valor: {adf_res[1]:.4e} ({'Estacionaria' if adf_res[1] < 0.05 else 'No estacionaria'})")

# Regresión Lineal por Mínimos Cuadrados a mano: beta = (X^T X)^(-1) X^T y
diario["t"] = np.arange(len(diario))
diario["dia_sem"] = diario.index.dayofweek
diario["es_quincena"] = diario.index.day.isin([15, 16, 30, 31, 1]).astype(int)

X_raw = diario[["t", "dia_sem", "es_quincena"]].values
y_reg = diario["autos"].values
X_b = np.c_[np.ones((len(X_raw), 1)), X_raw]

beta_manual = np.linalg.inv(X_b.T @ X_b) @ X_b.T @ y_reg
y_pred_manual = X_b @ beta_manual

lr_sklearn = LinearRegression().fit(X_raw, y_reg)
y_pred_sk = lr_sklearn.predict(X_raw)

print(f"Diferencia máxima NumPy vs scikit-learn: {np.max(np.abs(y_pred_manual - y_pred_sk)):.10f}")
print(f"Métricas Regresión -> RMSE: {np.sqrt(mean_squared_error(y_reg, y_pred_manual)):.2f} | MAE: {mean_absolute_error(y_reg, y_pred_manual):.2f} | R2: {r2_score(y_reg, y_pred_manual):.4f}")

print("\n=== E3: MODELO ARIMA(2,1,2) Y CLASIFICADORES CON F1 / MATRIZ DE CONFUSIÓN ===")
modelo_arima = ARIMA(diario["autos"], order=(2, 1, 2)).fit()
print(f"ARIMA(2,1,2) AIC: {modelo_arima.aic:.2f}")
pron = modelo_arima.get_forecast(steps=7)
print("Pronóstico 7 días:\n", pron.predicted_mean.round(1))

# Clasificación: Día de venta alta (1) vs normal (0)
umbral = diario["autos"].median()
y_clf = (diario["autos"] > umbral).astype(int)
X_train, X_test, y_train, y_test = train_test_split(X_raw, y_clf, test_size=0.2, random_state=42)

for nombre, clf in [
    ("Naive Bayes", GaussianNB()),
    ("KNN (k=5)", KNeighborsClassifier(n_neighbors=5)),
    ("Árbol de Decisión", DecisionTreeClassifier(max_depth=5, random_state=42)),
    ("Random Forest", RandomForestClassifier(n_estimators=100, random_state=42))
]:
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    print(f"\nModelo: {nombre} | F1-Score: {f1_score(y_test, preds):.4f}")
    print("Matriz de confusión:\n", confusion_matrix(y_test, preds))
