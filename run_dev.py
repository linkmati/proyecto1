import subprocess
import sys
import os
import signal
import threading

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

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "vinted-backend")
    frontend_dir = os.path.join(root_dir, "vinted-frontend")

    # Backend: uvicorn app.main:app --reload
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload"]
    # Frontend: npm run dev
    frontend_cmd = ["npm", "run", "dev"]

    print("🚀 Starting services...")

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
        print("\n🛑 Stopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    backend_proc.wait()
    frontend_proc.wait()

if __name__ == "__main__":
    main()
