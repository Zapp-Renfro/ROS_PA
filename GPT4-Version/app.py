from flask import Flask, request, render_template, jsonify
from diffusers import StableDiffusionPipeline
from datetime import datetime
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips, CompositeAudioClip
from gtts import gTTS
from supabase import create_client, Client
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
from PIL import Image
import numpy as np
import uuid
from rq import Queue
from rq.job import Job
from worker import conn
import logging
import time
from requests.exceptions import HTTPError
import boto3

HUGGINGFACE_API_TOKEN = "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"  # Remplacezm
API_URL_IMAGE = "https://api-inference.huggingface.co/models/dataautogpt3/ProteusV0.2"
API_URL_IMAGE_V2 = "https://api-inference.huggingface.co/models/alvdansen/BandW-Manga"

# Initialisation de l'application Flask
app = Flask(__name__)
q = Queue(connection=conn)

# Configuration de logging
logging.basicConfig(level=logging.DEBUG)

# Initialisation de Supabase
SUPABASE_URL = 'https://lpfjfbvhhckrnzdfezgd.supabase.co'  # Remplacez par votre URL Supabase sans slash finall
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwZmpmYnZoaGNrcm56ZGZlemdkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTY2NTYyMzEsImV4cCI6MjAzMjIzMjIzMX0.xXvve7bQ0lSz38CT9s9iQF3VlPo-vKbCy5Vw3Zhl84c'  # Remplacez par votre clé API publique
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS_LIST = [{"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}]


# Configuration AWS
AWS_ACCESS_KEY_ID = 'AKIAVRUVT3YMY5C23CNL'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = 'eu-west-1'

def text_to_speech(text, output_filename):
    # Initialiser le client Polly
    polly_client = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ).client('polly')

    # Convertir le texte en parole
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Joanna'  # Vous pouvez changer la voix ici
    )

    # Enregistrer le fichier audio
    with open(output_filename, 'wb') as file:
        file.write(response['AudioStream'].read())

def format_response(chat_history):
    formatted_text = ""
    for entry in chat_history:
        if entry['role'] == 'user':
            formatted_text += f"<b>Question:</b> {entry['content']}<br>"
        elif entry['role'] == 'assistant':
            formatted_text += f"<b>Réponse:</b> {entry['content']}<br><br>"
    return formatted_text

def generate_images_from_prompts(prompts, code):
    filenames = []
    max_retries = 5
    base_retry_delay = 5  # seconds

    for prompt in prompts:
        headers = random.choice(HEADERS_LIST)
        for attempt in range(max_retries):
            try:
                logging.debug(f"Sending request to Hugging Face API with prompt: {prompt}")
                response = requests.post(API_URL_IMAGE_V2, headers=headers, json={"inputs": prompt})
                logging.debug(f"Response status code: {response.status_code}")
                response.raise_for_status()

                if 'image' in response.headers['Content-Type']:
                    logging.debug("Response contains an image")
                    image_data = response.content
                    try:
                        image = Image.open(BytesIO(image_data))
                    except Exception as e:
                        logging.error(f"Error opening image: {e}")
                        continue

                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"image_{timestamp}.png"
                    filenames.append(filename)
                    logging.debug(f"Generated filename: {filename}")

                    # Convert image to binary data
                    with BytesIO() as img_byte_arr:
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        image_blob = img_byte_arr.read()

                    # Stocker l'image dans Supabase
                    data = {"prompt_text": prompt, "filename": filename, "image_blob": base64.b64encode(image_blob).decode('utf-8'), "code": code}
                    logging.debug(f"Data to insert into images: {data}")
                    try:
                        supabase.table('images').insert(data).execute()
                    except Exception as e:
                        logging.error(f"Error inserting data into Supabase: {e}")
                        continue
                    break
                else:
                    logging.error(f"Response did not contain an image: {response.content}")
            except HTTPError as err:
                logging.error(f"HTTP error occurred: {err}")
                if response.status_code == 503 and attempt < max_retries - 1:
                    retry_delay = base_retry_delay * (2 ** attempt)  # Exponential backoff
                    logging.debug(f"Retrying after {retry_delay} seconds due to 503 error...")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"Failed after {max_retries} attempts")
                    break
            except Exception as err:
                logging.error(f"An error occurred: {err}")
                break

    return filenames


def text_to_image(img_array, text, font_size=48, text_color=(255, 255, 255),
                  outline_color=(0, 0, 0), shadow_color=(50, 50, 50), max_width=None):
    logging.debug("Entering text_to_image function")
    image = Image.fromarray(img_array)
    draw = ImageDraw.Draw(image)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, font_size)
        logging.debug(f"Font loaded: {font_path} with size {font_size}")
    except IOError:
        font = ImageFont.load_default()
        logging.warning("Font not found, using default font")

    if max_width is None:
        max_width = image.width - 40  # Ajouter une marge de 20 pixels de chaque côté
    logging.debug(f"Max width for text: {max_width}")

    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        text_bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    logging.debug(f"Text split into lines: {lines}")

    total_text_height = sum(
        [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines])
    current_height = (image.height - total_text_height) / 2

    for line in lines:
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((image.width - text_width) / 2, current_height)
        logging.debug(f"Drawing text: {line} at position {text_position}")

        shadow_offset = 2
        draw.text((text_position[0] + shadow_offset, text_position[1] + shadow_offset), line, font=font,
                  fill=shadow_color)
        outline_range = 1
        for x in range(-outline_range, outline_range + 1):
            for y in range(-outline_range, outline_range + 1):
                if x != 0 or y != 0:
                    draw.text((text_position[0] + x, text_position[1] + y), line, font=font, fill=outline_color)
        draw.text(text_position, line, font=font, fill=text_color)

        current_height += text_height

    logging.debug("Exiting text_to_image function")
    return np.array(image)


def create_video_with_text(images_data, output_video, prompts, fps=1,
                           audio_path='static/music/relaxing-piano-201831.mp3'):
    audio_clips = []
    video_clips = []

    # Créer un répertoire pour stocker les fichiers audio
    audio_dir = 'static/audio'
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    for img_data, prompt in zip(images_data, prompts):
        audio_filename = os.path.join(audio_dir, f"{prompt[:10]}_audio.mp3")
        text_to_speech(prompt, audio_filename)
        speech_clip = AudioFileClip(audio_filename)

        # Convertir les données d'image en tableau NumPy
        image = Image.open(img_data).convert('RGBA')
        img_array = np.array(image)

        # Ajouter le texte directement sur l'image avec les améliorations
        img_with_text = text_to_image(img_array, prompt, font_size=48)

        img_clip = ImageClip(img_with_text).set_duration(speech_clip.duration)
        video = img_clip.set_audio(speech_clip)
        video_clips.append(video)
        audio_clips.append(speech_clip)

    if not video_clips:
        logging.error("No video clips were created. Ensure that image data and prompts are valid.")
        return

    final_video = concatenate_videoclips(video_clips, method="compose")
    background_music = AudioFileClip(audio_path).subclip(0, final_video.duration)
    background_music = background_music.volumex(0.4)

    final_audio = concatenate_audioclips(audio_clips)
    final_audio = CompositeAudioClip([background_music, final_audio.set_duration(background_music.duration)])
    final_video = final_video.set_audio(final_audio)

    # Écrire la vidéo finale dans un fichier
    final_video.write_videofile(output_video, fps=fps, codec='libx264')

    # Nettoyer les fichiers audio temporaires
    for audio_file in os.listdir(audio_dir):
        os.remove(os.path.join(audio_dir, audio_file))


@app.route('/', methods=['GET', 'POST'])
def generate_text():
    if request.method == 'POST':
        prompt = request.form['prompt']

        # Appel à l'API de Hugging Face avec le modèle gpt-neo-2.7B
        API_URL_TEXT = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
        API_TOKEN = "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"  # Remplacez par votre jeton API Hugging Face
        headers = {"Authorization": f"Bearer {API_TOKEN}"}

        # Log the request for debugging purposes
        logging.debug(f"Sending request to Hugging Face API with prompt: {prompt}")

        response = requests.post(API_URL_TEXT, headers=headers, json={"inputs": prompt})

        # Log the response status code and content for debugging purposes
        logging.debug(f"Hugging Face API response status: {response.status_code}")
        logging.debug(f"Hugging Face API response content: {response.content}")

        if response.status_code != 200:
            return jsonify({"error": "Failed to generate response from model"}), response.status_code

        response_json = response.json()
        logging.debug(f"Hugging Face API response JSON: {response_json}")

        # Handling different possible response structures
        if isinstance(response_json, list) and len(response_json) > 0 and 'generated_text' in response_json[0]:
            generated_text = response_json[0]['generated_text']
        else:
            generated_text = 'No response'

        # Stocker dans Supabase
        data = {"prompt": prompt, "response": generated_text}
        logging.debug(f"Data to insert into prompts: {data}")
        try:
            supabase.table('prompts').insert(data).execute()
        except Exception as e:
            logging.error(f"Error inserting data into prompts: {str(e)}")
            return jsonify({"error": str(e)}), 400

        return render_template('result.html', response=generated_text, image_prompt=generated_text)
    else:
        return render_template('index.html')

@app.route('/history', methods=['GET'])
def get_history():
    try:
        response = supabase.table('prompts').select('*').execute()
        return render_template('history.html', data=response.data)
    except Exception as e:
        logging.error(f"Error fetching data from prompts: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/generate_images', methods=['POST'])
def generate_images_route():
    text = request.form['text']
    logging.debug(f"Received text for image generation: {text}")
    prompts = [sentence.strip() for sentence in text.split('.') if sentence.strip()]
    logging.debug(f"Generated prompts: {prompts}")

    code = str(uuid.uuid4())

    # Déplacer la génération d'images vers une tâche en arrière-plan
    job = q.enqueue_call(
        func=generate_images_from_prompts, args=(prompts, code), result_ttl=5000
    )
    return render_template('image_result.html', job_id=job.get_id(), prompts=prompts, code=code)

@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    job = Job.fetch(job_id, connection=conn)
    if job.is_finished:
        # Fetch image URLs from Supabase
        code = job.args[1]
        response = supabase.table('images').select('image_blob').eq('code', code).execute()
        image_urls = []
        if response.data:
            for img in response.data:
                image_blob = img.get('image_blob')
                if image_blob:
                    image_urls.append(f"data:image/png;base64,{image_blob}")
        return jsonify({"image_urls": image_urls}), 200
    else:
        return "Still processing", 202

@app.route('/create_video', methods=['GET'])
def create_video_route():
    prompts = request.args.getlist('prompts')
    code = request.args.get('code')

    if not code:
        logging.error("No code provided for video creation.")
        return "No code provided", 400

    logging.info(f"Creating video for code: {code} with prompts: {prompts}")

    # Récupérer les images depuis Supabase avec le code
    response = supabase.table('images').select('image_blob').eq('code', code).execute()
    if response.data:
        images_data = []
        for img in response.data:
            image_blob = img.get('image_blob')
            if image_blob:
                try:
                    images_data.append(BytesIO(base64.b64decode(image_blob)))
                    logging.info(f"Image retrieved for code {code}")
                except Exception as e:
                    logging.error(f"Failed to decode image for code {code}: {e}")
    else:
        logging.error(f"No images found for code {code}.")
        images_data = []

    if not images_data:
        logging.error(f"No valid images found for code {code}.")
        return "No valid images found", 400

    output_video = 'static/videos/output_video.mp4'
    if not os.path.exists('static/videos'):
        os.makedirs('static/videos')

    # Créer la vidéo avec les images récupérées
    create_video_with_text(images_data, output_video, prompts, audio_path='static/music/relaxing-piano-201831.mp3')

    # Obtenir le lien de la vidéo stockée dans Supabase
    with open(output_video, 'rb') as video_file:
        video_blob = video_file.read()
    video_base64 = base64.b64encode(video_blob).decode('utf-8')

    video_data = {
        "filename": os.path.basename(output_video),
        "video_blob": video_base64
    }

    try:
        supabase.table('videos').insert(video_data).execute()
        video_url = f"data:video/mp4;base64,{video_base64}"
    except Exception as e:
        logging.error(f"Error inserting video data into Supabase: {e}")
        video_url = None

    return render_template('video_result.html', video_url=video_url)

# API Endpoints
@app.route('/api/generate_text', methods=['POST'])
def api_generate_text():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # Appel à l'API de Hugging Face avec le modèle gpt-neo-2.7B
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    API_TOKEN = "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"  # Remplacez par votre jeton API Hugging Face
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    # Log the request for debugging purposes
    logging.debug(f"Sending request to Hugging Face API with prompt: {prompt}")

    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    logging.debug(f"Hugging Face API response status: {response.status_code}")
    logging.debug(f"Hugging Face API response content: {response.content}")

    if response.status_code != 200:
        return jsonify({"error": "Failed to generate response from model"}), response.status_code

    response_json = response.json()
    logging.debug(f"Hugging Face API response JSON: {response_json}")

    # Handling different possible
    if isinstance(response_json, list) and len(response_json) > 0 and 'generated_text' in response_json[0]:
        generated_text = response_json[0]['generated_text']
    else:
        generated_text = 'No response'

    return jsonify({"response": generated_text}), 200

@app.route('/api/generate_images', methods=['POST'])
def api_generate_images():
    data = request.get_json()
    prompts = data.get('prompts', [])
    if not prompts:
        return jsonify({"error": "Prompts are required"}), 400

    code = str(uuid.uuid4())
    job = q.enqueue_call(
        func=generate_images_from_prompts, args=(prompts, code), result_ttl=5000
    )
    return jsonify({'job_id': job.get_id()}), 202

if __name__ == "__main__":
    app.run(debug=True)
