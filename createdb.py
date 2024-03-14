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

# Connexion à PostgreSQL en tant qu'utilisateur postgres
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    user=db_admin_user,
    password=db_admin_password
)
conn.autocommit = True  # Active l'autocommit pour que les commandes SQL soient exécutées immédiatement

# Création de la base de données
with conn.cursor() as cur:
    cur.execute(f"CREATE DATABASE {db_name}")

# Création de l'utilisateur
with conn.cursor() as cur:
    cur.execute(f"CREATE USER {db_admin_user} WITH PASSWORD '{db_admin_password}'")

# Donne à l'utilisateur tous les privilèges sur la base de données
with conn.cursor() as cur:
    cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_admin_user}")

# Ferme la connexion
conn.close()

print("Base de données et utilisateur créés avec succès !")