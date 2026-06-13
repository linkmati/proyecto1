import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
print(f"Probando: {url.split('@')[1]}") # Solo mostramos el host por seguridad

try:
    conn = psycopg2.connect(url, connect_timeout=5)
    print("¡¡¡CONECTADO POR FIN!!!")
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
