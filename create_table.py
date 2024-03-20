import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Récupère les informations de connexion à la base de données à partir des variables d'environnement
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_admin_user = os.getenv("DB_ADMIN_USER")
db_admin_password = os.getenv("DB_ADMIN_PASSWORD")
db_name = os.getenv("DB_NAME")
print("Database:", db_name)
# Connexion à PostgreSQL en tant qu'utilisateur postgres
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    user=db_admin_user,
    password=db_admin_password,
    dbname=db_name
)

# Création des tables
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            mot_de_passe VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicules (
            id SERIAL PRIMARY KEY,
            location VARCHAR(255),
            year INTEGER,
            kilometers_driven INTEGER,
            fuel_type VARCHAR(50),
            transmission BOOLEAN, -- Changer BOOLEAN à VARCHAR
            owner_type VARCHAR(50),
            mileage FLOAT,
            seats INTEGER,
            price_in_euro FLOAT,
            brand VARCHAR(255),
            model VARCHAR(255),
            engine_numeric FLOAT,
            power_numeric FLOAT,
            is_sold_new BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historique (
            id SERIAL PRIMARY KEY,
            utilisateur_id INTEGER REFERENCES utilisateurs(id),
            vehicule_id INTEGER REFERENCES vehicules(id),
            date_achat TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Changer DATE à TIMESTAMP
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

# Ferme la connexion
conn.close()

print("Tables créées avec succès !")