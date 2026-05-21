import subprocess
import time
import json
import os
import sys

def get_ngrok_url():
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:4040/api/tunnels") as response:
            data = json.loads(response.read().decode())
            for tunnel in data['tunnels']:
                if tunnel['config']['addr'].endswith(':8000'):
                    return tunnel['public_url']
    except Exception:
        pass
    return None

def main():
    print("🚀 Iniciando túneles de ngrok...")
    
    # Matar procesos previos de ngrok
    subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
    
    # Iniciar ngrok usando el archivo de configuración actualizado
    # Asegúrate de que ngrok.yml tenga ambos túneles definidos
    ngrok_cmd = ["npx", "ngrok", "start", "--all"]
    
    ngrok_proc = subprocess.Popen(ngrok_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("⏳ Esperando a que ngrok genere las URLs...")
    backend_url = None
    for _ in range(10):
        time.sleep(2)
        backend_url = get_ngrok_url()
        if backend_url:
            break
    
    if not backend_url:
        print("❌ No se pudo obtener la URL del Backend de ngrok.")
        ngrok_proc.terminate()
        return

    print(f"✅ Backend URL: {backend_url}")
    
    # Actualizar .env del frontend (o backend según corresponda)
    # En este proyecto, el frontend parece leer VITE_API_URL
    env_path = os.path.join("vinted-backend", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("VITE_API_URL="):
                    f.write(f"VITE_API_URL={backend_url}\n")
                else:
                    f.write(line)
        print(f"📝 Archivo {env_path} actualizado.")

    print("\n🌍 ¡Todo listo! Puedes acceder desde:")
    # Nota: El frontend suele estar en el puerto 5173
    print(f"🔗 Frontend: Usa la URL de ngrok para el puerto 5173")
    print(f"⚙️  API vinculada: {backend_url}")
    print("\nMantén este script ejecutándose para mantener los túneles abiertos. Presiona Ctrl+C para salir.")

    try:
        ngrok_proc.wait()
    except KeyboardInterrupt:
        print("\n👋 Cerrando túneles...")
        ngrok_proc.terminate()

if __name__ == "__main__":
    main()
