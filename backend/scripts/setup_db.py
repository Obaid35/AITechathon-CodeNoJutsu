import psycopg2
import os

DB_URL = "postgresql://postgres:2_CGF$Gy_#s_7BD@db.gdlnfnmcdlcarqrgjrol.supabase.co:5432/postgres"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")

def setup_database():
    print("Connecting to Supabase PostgreSQL...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"Reading SQL from {SCHEMA_PATH}...")
        with open(SCHEMA_PATH, 'r') as f:
            sql = f.read()
            
        print("Executing schema setup (creating pgvector, table, and RPC)...")
        cur.execute(sql)
        
        print("✅ Database setup complete! Your Supabase project is now ready for NaqsKAR.")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
    finally:
        if 'conn' in locals() and conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
