import subprocess
import time
import json
import os
import sys

def get_ngrok_url(target_addr_end):
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:4040/api/tunnels") as response:
            data = json.loads(response.read().decode())
            for tunnel in data['tunnels']:
                if tunnel['config']['addr'].endswith(target_addr_end):
                    return tunnel['public_url']
    except Exception:
        pass
    return None

def main():
    print("🚀 Iniciando túneles de ngrok...")
    subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
    ngrok_proc = subprocess.Popen(["npx", "ngrok", "start", "--all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("⏳ Esperando a que ngrok genere las URLs...")
    frontend_url = None
    for _ in range(15):
        time.sleep(2)
        frontend_url = get_ngrok_url(':5173')
        if frontend_url:
            break
    
    if not frontend_url:
        print("❌ No se pudo obtener la URL de ngrok.")
        ngrok_proc.terminate()
        return

    print(f"✅ Frontend URL: {frontend_url}")
    
    # En el modo proxy, el backend se accede por la misma URL
    backend_url = frontend_url 
    
    # Actualizar .env del frontend
    env_path = os.path.join("vinted-frontend", ".env")
    with open(env_path, "w") as f:
        f.write(f"VITE_API_URL={backend_url}\n")
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
