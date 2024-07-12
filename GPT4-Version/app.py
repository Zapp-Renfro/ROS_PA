import boto3
from flask import Flask, request, render_template, jsonify, session, url_for, redirect, flash
from datetime import datetime
import os

from moviepy.video.io.VideoFileClip import VideoFileClip
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
import requests
import base64
from io import BytesIO
import random
import numpy as np
import uuid
from rq import Queue
from rq.job import Job
from worker import conn
import logging
import time
from requests.exceptions import HTTPError
import tempfile

from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os


JAMENDO_CLIENT_ID = "1fe12850"


HUGGINGFACE_API_TOKEN = "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"  # Remplacez
API_URL_IMAGE = "https://api-inference.huggingface.co/models/dataautogpt3/ProteusV0.2"
API_URL_IMAGE_V2 = "https://api-inference.huggingface.co/models/alvdansen/BandW-Manga"
API_URL_IMAGE_V3 = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"


# Initialisation de l'application Flask

app = Flask(__name__)
q = Queue(connection=conn)
app.secret_key = 'votre_cle_secrete'

# Configuration de logging
logging.basicConfig(level=logging.DEBUG)

# Initialisation de Supabase
SUPABASE_URL = 'https://lpfjfbvhhckrnzdfezgd.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwZmpmYnZoaGNrcm56ZGZlemdkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTY2NTYyMzEsImV4cCI6MjAzMjIzMjIzMX0.xXvve7bQ0lSz38CT9s9iQF3VlPo-vKbCy5Vw3Zhl84c'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
HEADERS_LIST = [{"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}]

# Configuration AWS
AWS_ACCESS_KEY_ID = 'AKIAVRUVT3YMY5C23CNL'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = 'eu-west-1'
mood = "bad"

import os
import logging
from flask import Flask, request, jsonify
from rq import Queue
from worker import conn
from tasks import create_video_with_text, fetch_images





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
                response = requests.post(API_URL_IMAGE_V3, headers=headers, json={"inputs": prompt})
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



@app.route('/create_video', methods=['GET'])
def create_video():
    prompts = request.args.getlist('prompts')
    code = request.args.get('code')
    if not code:
        logging.error("No code provided for video creation.")
        return "No code provided", 400
    logging.info(f"Creating video for code: {code} with prompts: {prompts}")

    images_data = fetch_images(code)
    if not images_data:
        logging.error(f"No valid images found for code {code}.")
        return "No valid images found", 400

    output_video = 'static/videos/output_video.mp4'
    if not os.path.exists('static/videos'):
        os.makedirs('static/videos')

    # Enqueue the task
    job = q.enqueue(create_video_with_text, images_data, output_video, prompts, audio_path='static/music/relaxing-piano-201831.mp3', voice_id='Justin')
    return jsonify({"job_id": job.get_id()})

@app.route('/check_status/<job_id>', methods=['GET'])
def check_status(job_id):
    from rq.job import Job
    job = Job.fetch(job_id, connection=conn)
    return jsonify({"job_id": job.get_id(), "status": job.get_status()})



@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/use_text', methods=['POST'])
def use_text():
    prompt = request.form.get('prompt2')
    if prompt:
        # Enregistrer dans Supabase
        data = {"prompt": prompt, "response": prompt}
        try:
            result = supabase.table('prompts').insert(data).execute()
            generated_id = result.data[0]['id']  # Assume that the ID is returned in the response
            session['generated_id'] = generated_id  # Save the generated ID in the session (optional)
        except Exception as e:
            logging.error(f"Error inserting data into prompts: {str(e)}")
            return jsonify({"error": str(e)}), 400

        # Directement utiliser le texte fourni
        return render_template('result.html', response=prompt, image_prompt=prompt)
    else:
        return jsonify({"error": "Prompt is required"}), 400


@app.route('/generate_text', methods=['POST'])
def generate_text():
    if 'user_email' not in session:
        flash("Veuillez vous connecter pour utiliser cette fonctionnalité.", "error")
        return redirect(url_for('login'))
    prompt_start = request.form['prompt_start']
    prompt = request.form['prompt']
    full_prompt = f"{prompt_start} {prompt}"
    max_length = 1000  # Maximum number of characters
    min_length = 800  # Minimum number of characters
    API_URL_TEXT = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    API_TOKEN = "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"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    # Utiliser la fonction generate de Hugging Face pour définir les paramètres de génération
    data = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 1024,  # Ajusté pour une correspondance approximative avec le nombre de caractères
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "eos_token_id": None
        }
    }
    response = requests.post(API_URL_TEXT, headers=headers, json=data)
    if response.status_code != 200:
        return jsonify({"error": "Failed to generate response from model"}), response.status_code
    response_json = response.json()
    if isinstance(response_json, list) and len(response_json) > 0 and 'generated_text' in response_json[0]:
        generated_text = response_json[0]['generated_text']
    else:
        generated_text = 'No response'
    # Fonction pour nettoyer et ajuster le texte généré
    def clean_generated_text(text):
        # Supprimer la partie du prompt initial si elle est répétée dans le texte généré
        if text.startswith(full_prompt):
            text = text[len(full_prompt):].strip()
        # Assurez-vous que le texte a une longueur appropriée
        if len(text) < min_length:
            text += ' ...'  # Ajouter des points de suspension si le texte est trop court
        # Assurez-vous que le texte se termine par un point
        if not text.endswith('.'):
            last_sentence_end = text.rfind('.')
            if last_sentence_end != -1:
                text = text[:last_sentence_end + 1]
            else:
                text = text.rstrip('!?,') + '.'
        return text
    cleaned_text = clean_generated_text(generated_text)
    # Limiter le texte à la longueur maximale spécifiée
    if len(cleaned_text) > max_length:
        cleaned_text = cleaned_text[:max_length]
        # S'assurer que le texte tronqué se termine par un point
        if not cleaned_text.endswith('.'):
            last_sentence_end = cleaned_text.rfind('.')
            if last_sentence_end != -1:
                cleaned_text = cleaned_text[:last_sentence_end + 1]
            else:
                cleaned_text = cleaned_text.rstrip('!?,') + '.'
    data = {"prompt": full_prompt, "response": cleaned_text}
    try:
        result = supabase.table('prompts').insert(data).execute()
        generated_id = result.data[0]['id']
        session['generated_id'] = generated_id
    except Exception as e:
        logging.error(f"Error inserting data into prompts: {str(e)}")
        return jsonify({"error": str(e)}), 400
    return render_template('result.html', response=cleaned_text, image_prompt=cleaned_text)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        data = {
            "email": email,
            "password": hashed_password,
            "created_at": 'now()'
        }
        try:
            result = supabase.table('users').insert(data).execute()
            flash("Inscription réussie. Veuillez vous connecter.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Error inserting user into database: {str(e)}")
            flash("Une erreur est survenue lors de l'inscription. Veuillez réessayer.", "error")
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            response = supabase.table('users').select('*').eq('email', email).execute()
            if response.data:
                user = response.data[0]
                if check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['user_email'] = user['email']
                    flash("Connexion réussie.", "success")
                    return redirect(url_for('index'))
                else:
                    flash("Mot de passe incorrect.", "error")
            else:
                flash("Adresse email non trouvée.", "error")
        except Exception as e:
            logging.error(f"Error logging in user: {str(e)}")
            flash("Une erreur est survenue lors de la connexion. Veuillez réessayer.", "error")
    return render_template('login.html')


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
    job = q.enqueue_call(
        func=generate_images_from_prompts, args=(prompts, code), result_ttl=5000
    )
    return render_template('image_result.html', job_id=job.get_id(), prompts=prompts, code=code)



@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    job = Job.fetch(job_id, connection=conn)
    if job.is_finished:
        code = job.args[1]
        response = supabase.table('images').select('image_blob', 'prompt_text').eq('code', code).execute()
        image_data = []
        if response.data:
            for img in response.data:
                image_blob = img.get('image_blob')
                prompt_text = img.get('prompt_text')
                if image_blob:
                    image_data.append({
                        'image_url': f"data:image/png;base64,{image_blob}",
                        'prompt_text': prompt_text
                    })
        return jsonify({"image_data": image_data}), 200
    else:
        return "Still processing", 202


@app.route('/api/generate_text', methods=['POST'])
def api_generate_text():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    API_TOKEN = "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"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    logging.debug(f"Sending request to Hugging Face API with prompt: {prompt}")
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    logging.debug(f"Hugging Face API response status: {response.status_code}")
    logging.debug(f"Hugging Face API response content: {response.content}")
    if response.status_code != 200:
        return jsonify({"error": "Failed to generate response from model"}), response.status_code
    response_json = response.json()
    logging.debug(f"Hugging Face API response JSON: {response_json}")
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


