import requests
from PIL import Image
from io import BytesIO
import random

API_URL = "https://api-inference.huggingface.co/models/dataautogpt3/ProteusV0.4"
API_URL_V2 = "https://api-inference.huggingface.co/models/alvdansen/BandW-Manga"
API_URL_V3 = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"


# Différents en-têtes avec des jetons d'authentification
HEADERS1 = {"Authorization": "Bearer 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"}
HEADERS2 = {"Authorization": "Bearer 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"}
HEADERS3 = {"Authorization": "Bearer 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"}
# Ajoutez autant de HEADERS que nécessaire

# Liste des en-têtes
HEADERS_LIST = [HEADERS1]

def get_image_from_api(prompt):
    # Sélectionner un en-tête aléatoiredd
    headers = random.choice(HEADERS_LIST)

    try:
        # Envoyer la requête à l'API
        response = requests.post(API_URL_V3, headers=headers, json={"inputs": prompt})
        response.raise_for_status()

        # Lire l'image à partir de la réponse
        image_data = response.content
        image = Image.open(BytesIO(image_data))

        # Sauvegarder l'image localement
        image.save("output_image1.png")
        print("L'image a été sauvegardée sous le nom 'output_image3.png'")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")

# Exemple d'utilisation
prompt = "something about love that can be sweet,psychologique, extraordinary because of an encounter in life or a love story."
get_image_from_api(prompt)
