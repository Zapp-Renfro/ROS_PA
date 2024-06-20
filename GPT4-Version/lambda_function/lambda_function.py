import os
import json
import requests
from PIL import Image
from io import BytesIO
import base64
from supabase import create_client, Client


def lambda_handler(event, context):
    prompt = event['prompt']

    # API Hugging Face
    HUGGINGFACE_API_TOKEN = os.environ['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']
    SUPABASE_URL = os.environ['https://lpfjfbvhhckrnzdfezgd.supabase.co']
    SUPABASE_KEY = os.environ['eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwZmpmYnZoaGNrcm56ZGZlemdkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTY2NTYyMzEsImV4cCI6MjAzMjIzMjIzMX0.xXvve7bQ0lSz38CT9s9iQF3VlPo-vKbCy5Vw3Zhl84c']
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    response = requests.post("https://api-inference.huggingface.co/models/dataautogpt3/ProteusV0.4", headers=headers,
                             json={"inputs": prompt})
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps(f"Error: {response.text}")
        }

    image_data = base64.b64decode(response.json()['outputs'][0])
    image = Image.open(BytesIO(image_data))

    # Convert the image to bytes
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    image_bytes = buffer.read()

    # Upload the image to Supabase Storage
    bucket_name = "ROS-IMAGES"  # Replace with your Supabase bucket name
    image_filename = f"generated_images/{prompt.replace(' ', '_')}.png"

    try:
        supabase.storage().from_(bucket_name).upload(image_filename, image_bytes, {
            "content-type": "image/png"
        })
        image_url = supabase.storage().from_(bucket_name).get_public_url(image_filename)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failed to upload image to Supabase: {str(e)}")
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Image generated and saved to Supabase',
            'image_url': image_url
        })
    }
