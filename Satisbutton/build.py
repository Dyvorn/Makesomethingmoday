import os
import subprocess
import sys

def build():
    """
    Builds the Satisfying Buttons application using PyInstaller.
    """
    script_name = "satisfying_buttons.py"
    app_name = "Satisfying Buttons"
    
    # Check if the main script exists
    if not os.path.exists(script_name):
        print(f"Error: Main script '{script_name}' not found.")
        sys.exit(1)

    print("Starting build process with PyInstaller...")

    # PyInstaller command arguments
    command = [
        'pyinstaller',
        '--name', app_name,
        '--onefile',
        '--windowed',  # Hides the console window
        '--noconfirm', # Overwrite output directory without asking
        '--clean',     # Clean PyInstaller cache and remove temporary files
        # '--icon', 'path/to/your/icon.ico', # Uncomment and set your icon path
        script_name
    ]

    try:
        subprocess.run(command, check=True, shell=sys.platform == 'win32')
        print("\nBuild successful!")
        print(f"Executable created in: {os.path.join(os.getcwd(), 'dist')}")
    except subprocess.CalledProcessError as e:
        print(f"\nAn error occurred during the build process: {e}")
    except FileNotFoundError:
        print("\nError: 'pyinstaller' command not found.")
        print("Please install PyInstaller with: pip install pyinstaller")

if __name__ == "__main__":
    build()