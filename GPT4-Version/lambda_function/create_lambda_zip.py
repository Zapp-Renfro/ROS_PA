import os
import zipfile
import subprocess
import shutil

# Définir les dépendances
dependencies = [
    'requests',
    'pillow',
    'supabase'
]

# Créer un dossier temporaire pour installer les dépendances
os.makedirs('lambda_package', exist_ok=True)

# Installer les dépendances dans le dossier temporaire
for dep in dependencies:
    subprocess.run(['pip', 'install', dep, '-t', 'lambda_package'])

# Ajouter les fichiers de dépendances au fichier zip
with zipfile.ZipFile('lambda_function.zip', 'w') as z:
    for root, dirs, files in os.walk('lambda_package'):
        for file in files:
            z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), 'lambda_package'))

    # Ajouter le fichier lambda_function.py
    z.write('lambda_function.py')

# Nettoyer le dossier temporaire
shutil.rmtree('lambda_package')
