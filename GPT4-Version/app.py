from flask import Flask, request, render_template, url_for, jsonify
from diffusers import StableDiffusionPipeline
from datetime import datetime
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips, CompositeAudioClip
from gtts import gTTS
from supabase import create_client, Client
import logging
import requests
import base64
from io import BytesIO
from PIL import Image
import random
import shutil

HUGGINGFACE_API_TOKEN = "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"  # Remplacez
API_URL = "https://api-inference.huggingface.co/models/dataautogpt3/ProteusV0.4"

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de logging
logging.basicConfig(level=logging.DEBUG)

# Initialisation de Supabase
SUPABASE_URL = 'https://lpfjfbvhhckrnzdfezgd.supabase.co'  # Remplacez par votre URL Supabase sans slash final
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwZmpmYnZoaGNrcm56ZGZlemdkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTY2NTYyMzEsImV4cCI6MjAzMjIzMjIzMX0.xXvve7bQ0lSz38CT9s9iQF3VlPo-vKbCy5Vw3Zhl84c'  # Remplacez par votre clé API publique
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS_LIST = [{"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}]

def text_to_speech(text, output_filename):
    tts = gTTS(text=text, lang='en')
    tts.save(output_filename)

def format_response(chat_history):
    formatted_text = ""
    for entry in chat_history:
        if entry['role'] == 'user':
            formatted_text += f"<b>Question:</b> {entry['content']}<br>"
        elif entry['role'] == 'assistant':
            formatted_text += f"<b>Réponse:</b> {entry['content']}<br><br>"
    return formatted_text

def generate_images_from_prompts(prompts):
    images_dir = os.path.join('static', 'images')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    filenames = []
    for prompt in prompts:
        headers = random.choice(HEADERS_LIST)
        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
            response.raise_for_status()

            image_data = response.content
            image = Image.open(BytesIO(image_data))

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"image_{timestamp}.png"
            filepath = os.path.join(images_dir, filename)
            image.save(filepath)
            filenames.append(filepath)

            # Stocker l'image dans Supabase
            data = {"prompt_text": prompt, "filename": filename}
            logging.debug(f"Data to insert into images: {data}")
            supabase.table('images').insert(data).execute()
        except requests.exceptions.HTTPError as err:
            logging.error(f"HTTP error occurred: {err}")
        except Exception as err:
            logging.error(f"An error occurred: {err}")

    return filenames

def create_video_with_text(image_paths, output_video, prompts, fps=1, audio_path='path_to_your_audio.mp3'):
    audio_clips = []
    video_clips = []

    # Créer un répertoire pour stocker les fichiers audio
    audio_dir = os.path.join('static', 'audio')
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    for img_file, prompt in zip(image_paths, prompts):
        audio_filename = os.path.join(audio_dir, f"{os.path.splitext(os.path.basename(img_file))[0]}_audio.mp3")
        text_to_speech(prompt, audio_filename)
        speech_clip = AudioFileClip(audio_filename)

        img_clip = ImageClip(img_file).set_duration(speech_clip.duration)
        txt_clip = TextClip(prompt, fontsize=24, color='white', font='Arial').set_position(('center', 'center')).set_duration(speech_clip.duration)
        video = CompositeVideoClip([img_clip, txt_clip])
        video = video.set_audio(speech_clip)
        video_clips.append(video)
        audio_clips.append(speech_clip)

    final_video = concatenate_videoclips(video_clips, method="compose")
    background_music = AudioFileClip(audio_path).subclip(0, final_video.duration)
    background_music = background_music.volumex(0.4)

    final_audio = concatenate_audioclips(audio_clips)
    final_audio = CompositeAudioClip([background_music, final_audio.set_duration(background_music.duration)])
    final_video = final_video.set_audio(final_audio)

    final_video.write_videofile(output_video, fps=fps, codec='libx264')

    # Déplacer les images utilisées dans le dossier images_used
    used_images_dir = os.path.join('static', 'images_used')
    if not os.path.exists(used_images_dir):
        os.makedirs(used_images_dir)

    for img_file in image_paths:
        shutil.move(img_file, os.path.join(used_images_dir, os.path.basename(img_file)))

    # Nettoyer les fichiers audio temporaires
    for audio_file in os.listdir(audio_dir):
        os.remove(os.path.join(audio_dir, audio_file))

@app.route('/', methods=['GET', 'POST'])
def generate_text():
    if request.method == 'POST':
        prompt = request.form['prompt']

        # Appel à l'API de Hugging Face avec le modèle gpt-neo-2.7B
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
        API_TOKEN = "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"  # Remplacez par votre jeton API Hugging Face
        headers = {"Authorization": f"Bearer {API_TOKEN}"}

        # Log the request for debugging purposes
        logging.debug(f"Sending request to Hugging Face API with prompt: {prompt}")

        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

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
    prompts = [sentence.strip() for sentence in text.split('.') if sentence.strip()]
    image_filenames = generate_images_from_prompts(prompts)
    image_urls = [url_for('static', filename=f'images/{os.path.basename(f)}') for f in image_filenames]
    return render_template('image_result.html', image_urls=image_urls, prompts=prompts)

@app.route('/create_video', methods=['GET'])
def create_video_route():
    prompts = request.args.getlist('prompts')
    image_folder = 'static/images'
    output_video = 'static/videos/output_video.mp4'
    if not os.path.exists('static/videos'):
        os.makedirs('static/videos')

    image_paths = [os.path.join(image_folder, img) for img in sorted(os.listdir(image_folder)) if img.endswith(".png")]

    create_video_with_text(image_paths, output_video, prompts, audio_path='static/music/relaxing-piano-201831.mp3')
    video_url = url_for('static', filename='videos/output_video.mp4')
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

    image_filenames = generate_images_from_prompts(prompts)
    image_urls = [url_for('static', filename='images/' + f) for f in image_filenames]

    return jsonify({"image_urls": image_urls}), 200

if __name__ == '__main__':
    app.run(debug=True)
