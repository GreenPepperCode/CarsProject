import os
import csv
import psycopg2
from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool

load_dotenv()

def init_db():
    min_conn, max_conn = 2, 20
    dsn = f"dbname='{os.getenv('DB_NAME')}' user='{os.getenv('DB_ADMIN_USER')}' password='{os.getenv('DB_ADMIN_PASSWORD')}' host='{os.getenv('DB_HOST')}' port='{os.getenv('DB_PORT')}'"
    return SimpleConnectionPool(minconn=min_conn, maxconn=max_conn, dsn=dsn)

db_pool = init_db()

def insert_vehicles(vehicles):
    conn = db_pool.getconn()
    cursor = conn.cursor()
    skipped_rows = 0
    try:
        for vehicle in vehicles:
            if vehicle[6] == '' or vehicle[7] == '':
                skipped_rows += 1
                continue
            cursor.execute("""
                INSERT INTO vehicules (location, year, kilometers_driven, fuel_type, transmission, owner_type, mileage, seats, price_in_euro, brand, model, engine_numeric, power_numeric, is_sold_new)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, vehicle)
        conn.commit()
    except Exception as e:
        print(f"Error inserting vehicles: {e}")
    finally:
        cursor.close()
        db_pool.putconn(conn)
        print(f"{skipped_rows} rows skipped due to invalid values.")


def import_csv_to_db(csv_file_path):
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader)  # Skip the header row
        vehicles = []
        for row in reader:
            if len(row) != 14:  # Vérifiez que la ligne contient 14 colonnes
                print(f"Error: Row has {len(row)} columns instead of 14. Skipping this row.")
                continue
            vehicles.append(row)
        insert_vehicles(vehicles)

if __name__ == "__main__":
    csv_file_path = "Classeur1.csv"
    import_csv_to_db(csv_file_path)
