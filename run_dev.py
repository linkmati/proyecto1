import subprocess
import sys
import os
import signal
import threading
import time
import json
import urllib.request

def stream_output(pipe, prefix):
    try:
        while True:
            line = pipe.readline()
            if not line:
                break
            sys.stdout.write(f"{prefix} {line.strip()}\n")
            sys.stdout.flush()
    except Exception as e:
        sys.stderr.write(f"Error streaming {prefix}: {e}\n")

def get_ngrok_url():
    try:
        with urllib.request.urlopen("http://localhost:4040/api/tunnels") as response:
            data = json.loads(response.read().decode())
            for tunnel in data['tunnels']:
                # Exponemos el Frontend (5173) que ahora tiene el proxy configurado
                if tunnel['config']['addr'].endswith(':5173'):
                    return tunnel['public_url']
    except Exception:
        pass
    return None

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "vinted-backend")
    frontend_dir = os.path.join(root_dir, "vinted-frontend")

    print("🚀 [SYSTEM] Limpiando procesos previos...")
    subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
    # Limpiar puertos
    subprocess.run("lsof -i :8000 -i :5173 -t | xargs kill -9 2>/dev/null || true", shell=True)

    print("📡 [SYSTEM] Iniciando ngrok (Frontend + Proxy Backend)...")
    # Iniciamos solo el túnel del frontend. Usamos --host-header para que Vite no se queje.
    ngrok_proc = subprocess.Popen(
        ["npx", "ngrok", "http", "5173", "--host-header=localhost:5173"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Esperar URL de ngrok
    public_url = None
    for i in range(15):
        time.sleep(1)
        public_url = get_ngrok_url()
        if public_url:
            break
        if i % 5 == 0:
            print(f"[SYSTEM] Esperando ngrok ({i}/15)...")

    if public_url:
        print(f"[SYSTEM] Web pública lista: {public_url}")
        print(f"[SYSTEM] Abre esta URL en tu navegador.")
    else:
        print("[SYSTEM] No se pudo obtener URL de ngrok. Usando modo local.")

    # Backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload"]
    # Frontend
    frontend_cmd = ["npm", "run", "dev"]

    print("⚙️  [SYSTEM] Iniciando Backend y Frontend...")
    
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

    t1 = threading.Thread(target=stream_output, args=(backend_proc.stdout, "[\033[94mBACKEND\033[0m]"), daemon=True)
    t2 = threading.Thread(target=stream_output, args=(frontend_proc.stdout, "[\033[92mFRONTEND\033[0m]"), daemon=True)

    t1.start()
    t2.start()

    def signal_handler(sig, frame):
        print("\n👋 [SYSTEM] Cerrando todo...")
        backend_proc.terminate()
        frontend_proc.terminate()
        ngrok_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
