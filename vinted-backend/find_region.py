import psycopg2
import concurrent.futures

# Lista ampliada de regiones de Supabase (AWS)
regions = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2",
    "sa-east-1", "ca-central-1"
]

project_id = "gzsmtdgfgarwtmuhalrh"
password = "ymhhkp1TzQUUN5yN"

def try_region(r):
    host = f"aws-0-{r}.pooler.supabase.com"
    url = f"postgresql://postgres.{project_id}:{password}@{host}:6543/postgres"
    try:
        conn = psycopg2.connect(url, connect_timeout=3)
        conn.close()
        return r, url
    except Exception:
        return r, None

print(f"Buscando región para el proyecto {project_id}...")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(try_region, regions))

found = False
for r, url in results:
    if url:
        print(f"¡ENCONTRADA!: La región es {r}")
        print(f"URL: {url}")
        found = True
        # Actualizar .env
        with open(".env", "r") as f: lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("DATABASE_URL="): f.write(f"DATABASE_URL={url}\n")
                else: f.write(line)
        break

if not found:
    print("No se encontró el proyecto en ninguna región estándar de AWS.")
