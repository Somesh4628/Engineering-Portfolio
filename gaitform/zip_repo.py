import os
import zipfile

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        # Exclude unnecessary directories
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', '.git', 'temp_repo', 'temp_updates', 'temp_extract', '.pytest_cache', '.mypy_cache']]
        for file in files:
            if not file.endswith('.zip') and not file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                ziph.write(file_path, os.path.relpath(file_path, path))

if __name__ == '__main__':
    zip_path = 'd:/vs code/gaitform_final.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir('d:/vs code/gaitform', zipf)
    print(f"Created {zip_path}")
