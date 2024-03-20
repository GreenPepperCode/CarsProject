import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from fastapi import FastAPI, Depends, HTTPException, Request
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256
import joblib
import pandas as pd
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

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

# Fonction pour vérifier le mot de passe
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Fonction pour générer un token JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Modèle pour les informations d'authentification
class Token(BaseModel):
    access_token: str
    token_type: str

# Modèle pour la prédiction
class Prediction(BaseModel):
    prediction: str

class User(BaseModel):
    username: str
    email: str
    password: str

class UserInput(BaseModel):
    location: str
    year: int
    kilometer_driven: int
    transmission: bool
    owner_type: str
    mileage: float
    seats: int
    model: str
    engine: float
    power: float
    is_sold_new: bool

app = FastAPI(host="192.168.1.158")

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

@app.post("/users/", response_model=User)
def create_user(user: User, cursor: psycopg2.extensions.cursor = Depends(get_db)):
    # Vérifiez si l'utilisateur existe déjà
    cursor.execute("SELECT * FROM utilisateurs WHERE username = %s OR email = %s", (user.username, user.email))
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Hashez le mot de passe
    hashed_password = pbkdf2_sha256.hash(user.password)

    # Insérez l'utilisateur dans la base de données
    cursor.execute("INSERT INTO utilisateurs (username, email, mot_de_passe) VALUES (%s, %s, %s)", (user.username, user.email, hashed_password))
    cursor.connection.commit()

    return user

# Route pour l'authentification et la récupération du token
@app.post("/token", response_model=Token)
async def login_for_access_token(username: str, password: str, cursor: psycopg2.extensions.cursor = Depends(get_db)):
    # Vérification de l'identifiant et du mot de passe dans la base de données
    cursor.execute("SELECT * FROM utilisateurs WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user or not verify_password(password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Génération du token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Fonction pour valider le token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

@app.post('/predict')
async def predict(request: Request, current_user: str = Depends(get_current_user)):
    # Récupérer les données envoyées par le formulaire
    data = await request.json()

    # Convertir les données en un format approprié pour le modèle
    df = pd.DataFrame(data)

    # Effectuer une prédiction avec le modèle
    prediction = model.predict(df)

    # Retourner le résultat de la prédiction
    return {'prediction': prediction[0]}

# Récupérer toutes les marques
@app.get("/brands", response_model=List[str])
async def get_brands(cursor: psycopg2.extensions.cursor = Depends(get_db)):
    # Récupérer toutes les marques de véhicules de la base de données
    cursor.execute("SELECT DISTINCT brand FROM vehicules")
    brands = [row[0] for row in cursor.fetchall()]

    # Ajouter l'option "Autre" à la liste des marques
    brands.append("Autre")

    return brands

# Route dynamique pour récupérer le prix moyen des véhicules d'une marque spécifique
@app.get("/vehicles/{brand}", response_model=dict)
async def get_average_price_by_brand(brand: str, cursor: psycopg2.extensions.cursor = Depends(get_db)):
    # Récupère les données des véhicules de la marque spécifiée depuis la base de données
    cursor.execute("SELECT * FROM vehicules WHERE brand = %s", (brand,))
    vehicules = cursor.fetchall()

    if vehicules:
        # Calcule le prix moyen des véhicules de la marque
        average_price = sum([vehicule[9] for vehicule in vehicules]) / len(vehicules)
        return {"brand": brand, "average_price": average_price}
    else:
        return {"error": "Brand not found"}
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

@app.post("/users/", response_model=User)
def create_user(user: User, cursor: psycopg2.extensions.cursor = Depends(get_db)):
    # Vérifiez si l'utilisateur existe déjà
    cursor.execute("SELECT * FROM utilisateurs WHERE username = %s OR email = %s", (user.username, user.email))
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Hashez le mot de passe
    hashed_password = pbkdf2_sha256.hash(user.password)

    # Insérez l'utilisateur dans la base de données
    cursor.execute("INSERT INTO utilisateurs (username, email, mot_de_passe) VALUES (%s, %s, %s)", (user.username, user.email, hashed_password))
    cursor.connection.commit()

    return user

# Route pour l'authentification et la récupération du token
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Récupérez l'utilisateur de la base de données en utilisant son nom d'utilisateur
    cursor = db_pool.getconn().cursor()
    cursor.execute("SELECT * FROM utilisateurs WHERE username = %s", (form_data.username,))
    user = cursor.fetchone()

    # Vérifiez que l'utilisateur existe et que le mot de passe est correct
    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Créez un token d'accès pour l'utilisateur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[0]}, expires_delta=access_token_expires
    )

    # Retournez le token d'accès
    return {"access_token": access_token, "token_type": "bearer"}

# Fonction pour valider le token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# Route pour la prédiction
@app.post('/predict')
async def predict(request: Request, current_user: str = Depends(get_current_user)):
    # Récupérer les données envoyées par le formulaire
    data = await request.json()

    # Convertir les données en un format approprié pour le modèle
    df = pd.DataFrame(data)

    # Effectuer une prédiction avec le modèle
    prediction = model.predict(df)

    # Retourner le résultat de la prédiction
    return {'prediction': prediction[0]}

# Récupérer toutes les marques
@app.get("/brands", response_model=List[str])
async def get_brands(cursor: psycopg2.extensions.cursor = Depends(get_db)):
    # Récupérer toutes les marques de véhicules de la base de données
    cursor.execute("SELECT DISTINCT brand FROM vehicules")
    brands = [row[0] for row in cursor.fetchall()]

    # Ajouter l'option "Autre" à la liste des marques
    brands.append("Autre")

    return brands

# Route dynamique pour récupérer le prix moyen des véhicules d'une marque spécifique
@app.get("/vehicles/{brand}", response_model=dict)
async def get_average_price_by_brand(brand: str, cursor: psycopg2.extensions.cursor = Depends(get_db)):
    # Récupère les données des véhicules de la marque spécifiée depuis la base de données
    cursor.execute("SELECT * FROM vehicules WHERE brand = %s", (brand,))
    vehicules = cursor.fetchall()

    if vehicules:
        # Calcule le prix moyen des véhicules de la marque
        average_price = sum([vehicule[9] for vehicule in vehicules]) / len(vehicules)
        return {"brand": brand, "average_price": average_price}
    else:
        return {"error": "Brand not found"}