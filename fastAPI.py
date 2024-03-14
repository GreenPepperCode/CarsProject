from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Exemple de données de véhicules
fake_vehicle_data = {
    "Toyota": {"Corolla": 25000, "Camry": 30000},
    "Honda": {"Accord": 28000, "Civic": 26000}
}

# Configuration pour l'authentification JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fonctions pour l'authentification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fonction pour vérifier le mot de passe
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Fonction pour générer un token JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
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

app = FastAPI()

# Route pour l'authentification et la récupération du token
@app.post("/token", response_model=Token)
async def login_for_access_token(username: str, password: str):
    # Vérification de l'identifiant et du mot de passe (ceci est un exemple simple)
    if username != "user" or not verify_password(password, "password"):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Génération du token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Fonction pour valider le token
async def get_current_user(token: str = Depends()):
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

# Route pour effectuer une prédiction
@app.post("/predict", response_model=Prediction)
async def predict(data: dict, current_user: str = Depends(get_current_user)):
    # Ici, tu peux ajouter la logique pour effectuer la prédiction en utilisant ton modèle
    # Ceci est juste un exemple de réponse
    return {"prediction": "Your prediction goes here"}

# Route dynamique pour récupérer le prix moyen des véhicules d'une marque spécifique
@app.get("/vehicles/{brand}", response_model=dict)
async def get_average_price_by_brand(brand: str = Path(..., title="The brand of the vehicle")):
    # Vérifie si la marque existe dans les données fictives
    if brand in fake_vehicle_data:
        vehicles = fake_vehicle_data[brand]
        # Calcule le prix moyen des véhicules de la marque
        average_price = sum(vehicles.values()) / len(vehicles)
        return {"brand": brand, "average_price": average_price}
    else:
        return {"error": "Brand not found"}

# Route dynamique pour récupérer le prix moyen des véhicules d'un modèle spécifique
@app.get("/vehicles/{brand}/{model}", response_model=dict)
async def get_average_price_by_model(brand: str, model: str, current_user: str = Depends(get_current_user)):
    # Vérifie si la marque existe dans les données fictives
    if brand in fake_vehicle_data:
        vehicles = fake_vehicle_data[brand]
        # Vérifie si le modèle existe pour cette marque
        if model in vehicles:
            # Récupère le prix du modèle spécifique
            model_price = vehicles[model]
            return {"brand": brand, "model": model, "price": model_price}
        else:
            return {"error": "Model not found for this brand"}
    else:
        return {"error": "Brand not found"}