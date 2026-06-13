import subprocess
import sys
import os
import signal
import threading
import time

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

def main():
    # Directorios del proyecto
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "vinted-backend")
    frontend_dir = os.path.join(root_dir, "vinted-frontend")

    print("🚀 [SISTEMA] ¡Arrancando el proyecto de clase!")
    
    # 1. Limpieza de procesos viejos para que no den guerra
    print("🧹 [SISTEMA] Limpiando puertos antiguos...")
    subprocess.run(f"lsof -i :{BACKEND_PORT} -i :{FRONTEND_PORT} -t | xargs kill -9 2>/dev/null || true", shell=True)

    # 2. Lanzar el Backend y el Frontend a la vez
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
