import os
import boto3
import json
import requests
from PIL import Image
import io
import base64


# Configurer les variables d'environnement
HUGGINGFACE_API_TOKEN = os.environ['HUGGINGFACE_API_TOKEN']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']

# Configurer l'accès à S3
s3 = boto3.client('s3')

# Fonction Lambda principale
def lambda_handler(event, context):
    # Récupérer le texte à partir de l'événement d'entrée
    text = event['text']

    # Générer les images à partir de l'API Hugging Face
    images = generate_images_from_text(text)

    # Télécharger les images sur S3
    image_urls = upload_images_to_s3(images)

    # Stocker les URL d'images dans Supabase
    store_image_urls_in_supabase(image_urls)

    # Retourner une réponse réussie
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Images générées et stockées avec succès',
            'image_urls': image_urls
        })
    }

# Fonction pour générer des images à partir de l'API Hugging Face
def generate_images_from_text(text):
    # Configurer les en-têtes d'autorisation
    headers = {
        'Authorization': f'Bearer {HUGGINGFACE_API_TOKEN}'
    }

    # Envoyer une requête POST à l'API Hugging Face pour générer des images
    response = requests.post(
        'https://api-inference.huggingface.co/models/dataautogpt3/ProteusV0.4',
        headers=headers,
        json={
            'inputs': text
        }
    )

    # Vérifier que la réponse est réussie
    if response.status_code != 200:
        raise Exception(f'La requête à API Hugging Face a échoué avec le code d\'état {response.status_code}')

    # Extraire les images de la réponse et les convertir en objets PIL
    images = [Image.open(BytesIO(base64.b64decode(img_str))) for img_str in response.json()['outputs']]

    # Retourner les images
    return images

# Fonction pour télécharger les images sur S3
def upload_images_to_s3(images):
    # Générer des URL uniques pour chaque image
    image_urls = [f'{BUCKET_NAME}/{uuid}.png' for uuid in uuid.uuid4() for _ in images]

    # Convertir les objets PIL en données binaires
    image_data = [img.tobytes() for img in images]

    # Télécharger les données binaires sur S3 à l'aide des URL uniques
    for url, data in zip(image_urls, image_data):
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=url,
            Body=data,
            ContentType='image/png'
        )

    # Retourner les URL d'images
    return image_urls

# Fonction pour stocker les URL d'images dans Supabase
def store_image_urls_in_supabase(image_urls):
    # Configurer l'accès à Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Insérer les URL d'images dans la table d'images
    supabase.table('images').insert([
        {
            'url': url
        } for url in image_urls
    ]).execute()
