import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
import jwt
from pydantic import BaseModel
import joblib
import numpy as np
import shap
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

# JWT Configuration
SECRET_KEY = "tu_super_secreto_para_jwt_aqui"  # ¡En producción usar variables de entorno!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día

# Database Configuration (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

Base.metadata.create_all(bind=engine)

# Auth utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

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

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
def predict(data: PredictionInput, current_user: User = Depends(get_current_user)):
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