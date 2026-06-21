import os
import sys
import shutil
import subprocess

def main():
    # Resolve the absolute path of the directory containing run.py
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_dir, ".venv")
    
    # Switch working directory to project_dir to ensure relative paths align
    os.chdir(project_dir)
    
    print("=" * 60)
    print("         India Temperature Chatbot Bootstrapper")
    print("=" * 60)
    
    # Check if virtual environment exists but is broken (e.g. missing pip)
    # On Windows, pip is in Scripts/pip.exe, on Unix in bin/pip
    if sys.platform == "win32":
        pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
        uvicorn_executable = os.path.join(venv_dir, "Scripts", "uvicorn.exe")
    else:
        pip_executable = os.path.join(venv_dir, "bin", "pip")
        uvicorn_executable = os.path.join(venv_dir, "bin", "uvicorn")

    if os.path.exists(venv_dir) and not os.path.exists(pip_executable):
        print("Detected corrupted virtual environment (missing pip). Re-creating...")
        try:
            shutil.rmtree(venv_dir)
        except Exception as e:
            print(f"Error removing broken virtual env directory: {e}")
            print("Please manually delete the '.venv' directory and run this script again.")
            sys.exit(1)
            
    # 1. Create virtual environment if it doesn't exist
    if not os.path.exists(venv_dir):
        print(f"Creating python virtual environment in: {venv_dir}...")
        try:
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to create virtual environment. Details: {e}")
            sys.exit(1)
    else:
        print("Virtual environment (.venv) already exists.")
        
    # Re-verify/re-resolve paths after creation
    if sys.platform == "win32":
        pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
        uvicorn_executable = os.path.join(venv_dir, "Scripts", "uvicorn.exe")
    else:
        pip_executable = os.path.join(venv_dir, "bin", "pip")
        uvicorn_executable = os.path.join(venv_dir, "bin", "uvicorn")
        
    # Verify pip executable exists
    if not os.path.exists(pip_executable):
        print("Error: Virtual environment pip was not found. Please delete the '.venv' directory and run this script again.")
        sys.exit(1)
        
    # 3. Install requirements
    print("Installing required dependencies from requirements.txt...")
    try:
        subprocess.run([pip_executable, "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install dependencies. Details: {e}")
        sys.exit(1)
        
    # Verify uvicorn was installed
    if not os.path.exists(uvicorn_executable):
        print("Error: Uvicorn server was not found inside the virtual environment.")
        sys.exit(1)
        
    # 4. Start the FastAPI server
    print("\n" + "=" * 60)
    print(" Launching India Temperature Chatbot Server...")
    print(" Please open your browser and navigate to:")
    print(" --> http://127.0.0.1:8000")
    print("=" * 60 + "\n")
    
    try:
        # Start uvicorn
        subprocess.run([uvicorn_executable, "backend:app", "--host", "127.0.0.1", "--port", "8000"], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user (Ctrl+C). Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"\nServer exited with an error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
