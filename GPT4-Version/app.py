import boto3
from flask import Flask, request, render_template, jsonify, session, url_for, redirect
from datetime import datetime
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, \
    concatenate_audioclips, CompositeAudioClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from supabase import create_client, Client
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
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
def search_music_by_mood(mood):
    url = "https://api.jamendo.com/v3.0/tracks"
    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "limit": 10,
        "tags": mood
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Error: ", response.status_code)
        print(response.text)
        return None
    return response.json()
def get_video_duration(video_path):
    with VideoFileClip(video_path) as video:
        return int(video.duration)


def download_audio_preview(url):
    response = requests.get(url)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name
    return None
def upload_video_to_supabase(file_path, file_name):
    with open(file_path, 'rb') as file:
        res = supabase.storage().from_('videos').upload(file_name, file)
    return res
def text_to_speech(text, output_filename, voice_id='Miguel'):
    logging.debug(f"Using voice_id: {voice_id}")
    polly_client = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    ).client('polly')
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId=voice_id
    )

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
                    data = {"prompt_text": prompt, "filename": filename,
                            "image_blob": base64.b64encode(image_blob).decode('utf-8'), "code": code}
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


def create_video_with_text(images_data, output_video, prompts, fps=1, audio_path='static/music/relaxing-piano-201831.mp3', voice_id='Miguel'):
    audio_clips = []
    video_clips = []
    audio_dir = 'static/audio'
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
    for audio_file in os.listdir(audio_dir):
        os.remove(os.path.join(audio_dir, audio_file))
    for img_data, prompt in zip(images_data, prompts):
        audio_filename = os.path.join(audio_dir, f"{prompt[:10]}_audio.mp3")
        text_to_speech(prompt, audio_filename, voice_id)
        speech_clip = AudioFileClip(audio_filename)
        image = Image.open(img_data).convert('RGBA')
        img_array = np.array(image)
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
    final_video.write_videofile(output_video, fps=fps, codec='libx264')
    for audio_file in os.listdir(audio_dir):
        os.remove(os.path.join(audio_dir, audio_file))


@app.route('/create_video', methods=['GET'])
def create_video():
    prompts = request.args.getlist('prompts')
    code = request.args.get('code')
    if not code:
        logging.error("No code provided for video creation.")
        return "No code provided", 400
    logging.info(f"Creating video for code: {code} with prompts: {prompts}")
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
    create_video_with_text(images_data, output_video, prompts, audio_path='static/music/relaxing-piano-201831.mp3',
                           voice_id='Miguel')

    session['video_path'] = output_video
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
    if request.method == 'POST':
        prompt = request.form['prompt']
        prompt_size = len(prompt)
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
            generated_text = response_json[0]['generated_text'][prompt_size:] # coupe le prompt au début
            sentence_end_index = generated_text.rfind('.')
            generated_text = generated_text[:sentence_end_index + 1]
        else:
            generated_text = 'No response'
        # Stocker dans Supabase
        data = {"prompt": prompt, "response": generated_text}
        logging.debug(f"Data to insert into prompts: {data}")
        try:
            result = supabase.table('prompts').insert(data).execute()
            generated_id = result.data[0]['id']  # Assume that the ID is returned in the response
            session['generated_id'] = generated_id
        except Exception as e:
            logging.error(f"Error inserting data into prompts: {str(e)}")
            return jsonify({"error": str(e)}), 400
        return render_template('result.html', response=generated_text, image_prompt=generated_text)
    else:
        return render_template('index.html')


@app.route('/regenerate_image', methods=['POST'])
def regenerate_image():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # Utiliser le prompt pour générer une nouvelle image
    headers = random.choice(HEADERS_LIST)
    response = requests.post(API_URL_IMAGE_V3, headers=headers, json={"inputs": prompt})

    if response.status_code != 200:
        return jsonify({"error": "Failed to generate image"}), response.status_code

    image_data = response.content
    try:
        image = Image.open(BytesIO(image_data))
    except Exception as e:
        logging.error(f"Error opening image: {e}")
        return jsonify({"error": "Failed to open image"}), 500

    # Convertir l'image en URL de base64
    with BytesIO() as img_byte_arr:
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        image_base64 = base64.b64encode(img_byte_arr.read()).decode('utf-8')

    image_url = f"data:image/png;base64,{image_base64}"

    # Mettre à jour l'image dans Supabase
    try:
        supabase.table('images').delete().eq('prompt_text', prompt).execute()
        data = {
            "prompt_text": prompt,
            "image_blob": image_base64,
            "filename": f"{uuid.uuid4()}.png"
        }
        supabase.table('images').insert(data).execute()
    except Exception as e:
        logging.error(f"Error updating image in Supabase: {e}")
        return jsonify({"error": "Failed to update image in Supabase"}), 500

    return jsonify({"image_url": image_url}), 200


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


@app.route('/music_choice', methods=['GET', 'POST'])
def music_choice():
    mood_tracks = []
    search_tracks = []
    error = None
    try:
        # Définir une humeur par défaut
        mood = 'sad'  # Remplacez 'sad' par une méthode pour récupérer la véritable humeur si nécessaire
        app.logger.info(f'Retrieving tracks for mood: {mood}')
        # Récupérer les pistes pour l'humeur "sad"
        mood_result = search_music_by_mood(mood)
        if mood_result and 'results' in mood_result:
            mood_tracks = mood_result['results']
            app.logger.info(f'Found {len(mood_tracks)} tracks for mood: {mood}')
        else:
            error = "Aucune piste trouvée pour l'humeur donnée."
            app.logger.error(error)
        # Si une recherche par mot-clé est effectuée
        if request.method == 'POST':
            query = request.form.get('query')
            app.logger.info(f'Search query: {query}')
            if query:
                search_result = search_music_by_mood(query)
                if search_result:
                    search_tracks = search_result['results']
                    app.logger.info(f'Found {len(search_tracks)} tracks for search query: {query}')
                else:
                    error = "Aucune piste trouvée pour la recherche."
                    app.logger.error(error)
    except Exception as e:
        app.logger.exception(f"Error in /music_choice route: {e}")
        error = "Une erreur est survenue. Veuillez réessayer plus tard."
    return render_template('music_choice.html', mood=mood, mood_tracks=mood_tracks, search_tracks=search_tracks, error=error)



@app.route('/select_track', methods=['POST'])
def select_track():
    track_id = request.form.get('track_id')
    track_name = request.form.get('track_name')
    artist_name = request.form.get('artist_name')
    preview_url = request.form.get('preview_url')

    # Path to the existing video file
    video_path = session.get('video_path')
    if not os.path.exists(video_path):
        return "Fichier vidéo non trouvé.", 404
    # Get the duration of the existing video
    video_duration = get_video_duration(video_path)
    return render_template('play.html', track_id=track_id, track_name=track_name, artist_name=artist_name,
                           preview_url=preview_url, video_duration=video_duration)


@app.route('/final_video', methods=['POST'])
def final_video():
    track_id = request.form.get('track_id')
    preview_url = request.form.get('preview_url')
    music_start_time = int(request.form.get('start_time'))
    music_end_time = int(request.form.get('end_time'))

    # Path to the existing video file
    video_path = session.get('video_path')
    if not os.path.exists(video_path):
        return "Fichier vidéo non trouvé.", 404

    # Get the duration of the existing video
    video_duration = get_video_duration(video_path)

    # Calculate the duration of the selected music segment
    music_segment_duration = music_end_time - music_start_time

    # Ensure the selected segment duration does not exceed the video duration
    if music_segment_duration > video_duration:
        return "La durée de la sélection de la musique dépasse la durée de la vidéo.", 400

    # Ensure the selected segment is valid
    if music_end_time <= music_start_time:
        return "Temps de début ou de fin invalide.", 400

    # Download the audio preview
    audio_path = download_audio_preview(preview_url)
    if not audio_path:
        return "Aperçu audio non trouvé.", 404

    # Retrieve the generated text using the ID from the session
    generated_id = session.get('generated_id')
    if not generated_id:
        return "ID du texte généré non trouvé dans la session.", 400

    try:
        response = supabase.table('prompts').select('response').eq('id', generated_id).execute()
        if response.data:
            generated_text = response.data[0]['response']
        else:
            return "Aucun texte généré trouvé.", 404
    except Exception as e:
        logging.error(f"Error fetching generated text from Supabase: {e}")
        return "Erreur lors de la récupération du texte généré.", 500

    # Use text_to_speech to convert the text to speech
    voice_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    try:
        text_to_speech(generated_text, voice_audio_path, voice_id='Miguel')
    except Exception as e:
        logging.error(f"Error generating speech from text: {e}")
        return "Erreur lors de la génération de la voix à partir du texte.", 500

    # Create a temporary file for the new video with audio
    output_video_path = video_path
    audio_clip = None
    voice_clip = None
    try:
        # Load the existing video clip
        video_clip = VideoFileClip(video_path)

        # Add the audio file to the video
        audio_clip = AudioFileClip(audio_path).subclip(music_start_time, music_end_time)

        # Add the generated voice clip to the video
        voice_clip = AudioFileClip(voice_audio_path)
        final_audio = CompositeAudioClip([audio_clip.volumex(0.4), voice_clip.set_duration(video_clip.duration)])
        video_clip = video_clip.set_audio(final_audio)
        # Write the new video file
        video_clip.write_videofile(output_video_path, codec="libx264", fps=24)
        session['new_video_path'] = output_video_path
    finally:
        # Ensure the audio files are closed and deleted
        if audio_clip:
            audio_clip.close()
        if voice_clip:
            voice_clip.close()
        os.remove(audio_path)
        os.remove(voice_audio_path)

    # Save the new video to Supabase
    with open(output_video_path, 'rb') as video_file:
        video_blob = video_file.read()
    video_base64 = base64.b64encode(video_blob).decode('utf-8')
    video_data = {
        "filename": os.path.basename(output_video_path),
        "video_blob": video_base64
    }

    try:
        supabase.table('videos').insert(video_data).execute()
        video_url = f"data:video/mp4;base64,{video_base64}"
    except Exception as e:
        logging.error(f"Error inserting video data into Supabase: {e}")
        video_url = None

    return redirect(url_for('show_video'))




@app.route('/show_video')
def show_video():
    video_path = session.get('new_video_path')
    if not video_path or not os.path.exists(video_path):
        return "Vidéo non trouvée.", 404
    return render_template('show_video.html', video_path=video_path)
if __name__ == "__main__":
    app.run(debug=True)