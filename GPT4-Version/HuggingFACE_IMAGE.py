import requests
from PIL import Image
from io import BytesIO
import random

API_URL = "https://api-inference.huggingface.co/models/dataautogpt3/ProteusV0.4"

# Différents en-têtes avec des jetons d'authentification
HEADERS1 = {"Authorization": "Bearer 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"}
#HEADERS2 = {"Authorization": "Bearer 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"}
# Ajoutez autant de HEADERS que nécessaire

# Liste des en-têtes
HEADERS_LIST = [HEADERS1]

def get_image_from_api(prompt):
    # Sélectionner un en-tête aléatoire
    headers = random.choice(HEADERS_LIST)

    try:
        # Envoyer la requête à l'API
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        response.raise_for_status()

        # Lire l'image à partir de la réponse
        image_data = response.content
        image = Image.open(BytesIO(image_data))

        # Sauvegarder l'image localement
        image.save("output_image8.png")
        print("L'image a été sauvegardée sous le nom 'output_image3.png'")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")

# Exemple d'utilisation
prompt = "Le plus beau boss de jeu vidéo"
get_image_from_api(prompt)
