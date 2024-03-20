import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from fastapi import FastAPI, Depends, HTTPException, Request
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256
from sklearn.ensemble import GradientBoostingRegressor
import joblib
import pandas as pd
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Charger le modèle PKL
model = joblib.load('reg_model_final_GBR.pkl')

# Configuration pour l'authentification JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Fonctions pour l'authentification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class Hyperparameters(BaseModel):
    n_estimators: int = Field(default=100)
    learning_rate: float = Field(default=0.1)
    max_depth: int = Field(default=1)
    random_state: int = Field(default=42)
    loss: str = Field(default='ls')

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str
    password: str

def init_db():
    min_conn, max_conn = 2, 10
    dsn = f"dbname='{os.getenv('DB_NAME')}' user='{os.getenv('DB_USER')}' password='{os.getenv('DB_PASSWORD')}' host='{os.getenv('DB_HOST')}' port='{os.getenv('DB_PORT')}'"
    return SimpleConnectionPool(minconn=min_conn, maxconn=max_conn, dsn=dsn)

db_pool = init_db()

def get_db():
    conn = db_pool.getconn()
    try:
        yield conn.cursor()
    finally:
        conn.close()

class Vehicle(BaseModel):
    brand: str
    model: str
    year: int
    kilometer_driven: int
    transmission: bool
    owner_type: str
    mileage: float
    engine: float
    power: float
    price: float
    is_sold_new: bool

app = FastAPI()

@app.post("/train")
async def train_model(request: Request, hyperparameters: Hyperparameters, current_user: str = Depends(get_current_user)):
    """
    Entraîne le modèle avec les données fournies dans la requête et les hyperparamètres spécifiés.
    """
    data = await request.json()
    X = pd.DataFrame(data.get("X"))
    y = pd.DataFrame(data.get("y"))

    # Entraîner le modèle avec les hyperparamètres choisis
    model = GradientBoostingRegressor(n_estimators=hyperparameters.n_estimators, learning_rate=hyperparameters.learning_rate, max_depth=hyperparameters.max_depth, random_state=hyperparameters.random_state, loss=hyperparameters.loss)
    model.fit(X, y)

    # Sauvegarder le modèle entraîné
    joblib.dump(model, 'reg_model_final_GBR.pkl')

    return {"message": "Le modèle a été entraîné avec succès"}

@app.post("/vehicles/", response_model=Vehicle)
async def create_vehicle(vehicle: Vehicle, cursor: psycopg2.extensions.cursor = Depends(get_db)):
    """
    Ajoute un nouveau véhicule à la base de données.
    """
    # Vérifier si le véhicule existe déjà
    cursor.execute("SELECT * FROM vehicules WHERE brand = %s AND model = %s AND year = %s",
                   (vehicle.brand, vehicle.model, vehicle.year))
    existing_vehicle = cursor.fetchone()
    if existing_vehicle:
        raise HTTPException(status_code=400, detail="Le véhicule existe déjà")

    cursor.execute("INSERT INTO vehicules (brand, model, year, kilometer_driven, transmission, owner_type, mileage, engine, power, price, is_sold_new) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                   (vehicle.brand, vehicle.model, vehicle.year, vehicle.kilometer_driven, vehicle.transmission, vehicle.owner_type, vehicle.mileage, vehicle.engine, vehicle.power, vehicle.price, vehicle.is_sold_new))
    cursor.connection.commit()
    return vehicle

@app.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, cursor: psycopg2.extensions.cursor = Depends(get_db)):
    """
    Supprime un véhicule de la base de données.
    """
    # Vérifier si le véhicule existe
    cursor.execute("SELECT * FROM vehicules WHERE id = %s", (vehicle_id,))
    existing_vehicle = cursor.fetchone()
    if not existing_vehicle:
        raise HTTPException(status_code=404, detail="Le véhicule n'existe pas")

    cursor.execute("DELETE FROM vehicules WHERE id = %s", (vehicle_id,))
    cursor.connection.commit()
    return {"message": "Le véhicule a été supprimé avec succès"}

@app.get("/vehicles/", response_model=List[Vehicle])
async def get_vehicles(cursor: psycopg2.extensions.cursor = Depends(get_db)):
    """
    Récupère tous les véhicules de la base de données.
    """
    cursor.execute("SELECT * FROM vehicules")
    vehicles = cursor.fetchall()

    # Convertir les résultats en liste de dictionnaires
    vehicles_dict = []
    for vehicle in vehicles:
        vehicles_dict.append({
            "id": vehicle[0],
            "brand": vehicle[1],
            "model": vehicle[2],
            "year": vehicle[3],
            "kilometer_driven": vehicle[4],
            "transmission": vehicle[5],
            "owner_type": vehicle[6],
            "mileage": vehicle[7],
            "engine": vehicle[8],
            "power": vehicle[9],
            "price": vehicle[10],
            "is_sold_new": vehicle[11]
        })

    return vehicles_dict
