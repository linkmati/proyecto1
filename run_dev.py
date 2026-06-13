import subprocess
import sys
import os
import signal
import threading
import time
import json
import urllib.request

# --- CONFIGURACIÓN ---
BACKEND_PORT = "8000"
FRONTEND_PORT = "5173"

def stream_output(pipe, prefix):
    """Función para sacar por pantalla lo que dicen el backend y el frontend."""
    try:
        while True:
            line = pipe.readline()
            if not line:
                break
            # Limpiamos espacios y sacamos la línea con su prefijo de color
            sys.stdout.write(f"{prefix} {line.strip()}\n")
            sys.stdout.flush()
    except Exception:
        pass

def get_ngrok_url():
    """Intenta pillar la URL pública de ngrok si está funcionando."""
    try:
        with urllib.request.urlopen("http://localhost:4040/api/tunnels") as response:
            data = json.loads(response.read().decode())
            for tunnel in data['tunnels']:
                if tunnel['config']['addr'].endswith(f':{FRONTEND_PORT}'):
                    return tunnel['public_url']
    except Exception:
        return None

def main():
    # Directorios del proyecto
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "vinted-backend")
    frontend_dir = os.path.join(root_dir, "vinted-frontend")

    print("🚀 [SISTEMA] ¡Arrancando el proyecto de clase!")
    
    # 1. Limpieza de procesos viejos para que no den guerra
    print("🧹 [SISTEMA] Limpiando puertos y procesos antiguos...")
    subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
    # Matamos lo que haya en los puertos 8000 y 5173
    subprocess.run(f"lsof -i :{BACKEND_PORT} -i :{FRONTEND_PORT} -t | xargs kill -9 2>/dev/null || true", shell=True)

    # 2. Intentar arrancar ngrok (opcional, por si quieres que lo vea el profe desde su casa)
    print("📡 [SISTEMA] Lanzando ngrok para la web pública...")
    ngrok_proc = None
    try:
        ngrok_proc = subprocess.Popen(
            ["npx", "ngrok", "http", FRONTEND_PORT, "--host-header=localhost:5173"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Esperamos un poco a que ngrok nos dé la URL
        for i in range(10):
            time.sleep(1)
            url = get_ngrok_url()
            if url:
                print(f"🌍 [SISTEMA] ¡WEB LISTA EN INTERNET!: {url}")
                break
            if i == 9:
                print("⚠️  [SISTEMA] ngrok no responde, usaremos solo modo local.")
    except Exception:
        print("ℹ️  [SISTEMA] Saltando ngrok (no parece estar instalado).")

    # 3. Lanzar el Backend y el Frontend a la vez
    print("⚙️  [SISTEMA] Iniciando Backend y Frontend... (Ten paciencia)")
    
    # Backend: usamos el mismo python que ejecuta este script
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", BACKEND_PORT, "--reload"]
    # Frontend: comando normal de npm
    frontend_cmd = ["npm", "run", "dev"]

    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Hilos para ver los logs en una sola pantalla
        t1 = threading.Thread(target=stream_output, args=(backend_proc.stdout, "[\033[94mBACKEND\033[0m]"), daemon=True)
        t2 = threading.Thread(target=stream_output, args=(frontend_proc.stdout, "[\033[92mFRONTEND\033[0m]"), daemon=True)

        t1.start()
        t2.start()

        print(f"\n✅ [SISTEMA] Backend en: http://localhost:{BACKEND_PORT}")
        print(f"✅ [SISTEMA] Frontend en: http://localhost:{FRONTEND_PORT}")
        print("\n--- PULSA CTRL+C PARA CERRAR TODO ---\n")

        # Manejador para cerrar todo bien cuando hagamos Ctrl+C
        def cerrar_todo(sig, frame):
            print("\n\n👋 [SISTEMA] Cerrando procesos... ¡Hasta luego!")
            backend_proc.terminate()
            frontend_proc.terminate()
            if ngrok_proc:
                ngrok_proc.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, cerrar_todo)
        signal.signal(signal.SIGTERM, cerrar_todo)

        # Bucle infinito para mantener el script vivo
        while True:
            time.sleep(1)
            # Si alguno de los dos muere, avisamos
            if backend_proc.poll() is not None:
                print("❌ [SISTEMA] El Backend se ha parado inesperadamente.")
                break
            if frontend_proc.poll() is not None:
                print("❌ [SISTEMA] El Frontend se ha parado inesperadamente.")
                break

    except Exception as e:
        print(f"💥 [SISTEMA] Error fatal al arrancar: {e}")
        if 'backend_proc' in locals(): backend_proc.terminate()
        if 'frontend_proc' in locals(): frontend_proc.terminate()

if __name__ == "__main__":
    main()
