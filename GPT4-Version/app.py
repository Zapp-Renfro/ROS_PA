from flask import Flask, request, render_template, url_for
from gpt4all import GPT4All
import torch
from diffusers import StableDiffusionPipeline
from datetime import datetime
import os
from moviepy.editor import ImageSequenceClip

app = Flask(__name__)

def format_response(chat_history):
    formatted_text = ""
    for entry in chat_history:
        if entry['role'] == 'user':
            formatted_text += f"<b>Question:</b> {entry['content']}<br>"
        elif entry['role'] == 'assistant':
            formatted_text += f"<b>Réponse:</b> {entry['content']}<br><br>"
    return formatted_text

def generate_images_from_prompts(prompts):
    pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", safety_checker=None)
    pipe.enable_sequential_cpu_offload()
    pipe.enable_attention_slicing("max")

    images_dir = os.path.join('static', 'images')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    filenames = []
    for prompt in prompts:
        image = pipe(prompt).images[0]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"image_{timestamp}.png"
        filepath = os.path.join(images_dir, filename)
        image.save(filepath)
        filenames.append(filename)  # Just the filename

    return filenames

def create_video(image_folder, output_video, fps=1):
    image_files = [os.path.join(image_folder, img) for img in sorted(os.listdir(image_folder)) if img.endswith(".png")]
    if not image_files:
        return None  # No images to create a video
    clip = ImageSequenceClip(image_files, fps=fps)
    clip.write_videofile(output_video, codec='libx264')
    return output_video

@app.route('/', methods=['GET', 'POST'])
def generate_text():
    if request.method == 'POST':
        prompt = request.form['prompt']
        model = GPT4All(model_name='orca-mini-3b-gguf2-q4_0.gguf')
        with model.chat_session():
            response = model.generate(prompt=prompt)
            chat_history = model.current_chat_session
        formatted_response = format_response(chat_history)
        last_response = chat_history[-1]['content'] if chat_history and chat_history[-1]['role'] == 'assistant' else "Please generate a response first."
        return render_template('result.html', response=formatted_response, image_prompt=last_response)
    else:
        return render_template('index.html')

@app.route('/generate_images', methods=['POST'])
def generate_images_route():
    text = request.form['text']
    prompts = [sentence.strip() for sentence in text.split('.') if sentence.strip()]
    image_filenames = generate_images_from_prompts(prompts)
    image_urls = [url_for('static', filename='images/' + f) for f in image_filenames]
    return render_template('image_result.html', image_urls=image_urls)

@app.route('/create_video', methods=['GET'])
def create_video_route():
    image_folder = 'static/images'
    output_video = 'static/videos/output_video.mp4'
    if not os.path.exists('static/videos'):
        os.makedirs('static/videos')  # Crée le dossier s'il n'existe pas
    video_creation = create_video(image_folder, output_video)
    if video_creation:
        video_url = url_for('static', filename='videos/output_video.mp4')
        return render_template('video_result.html', video_url=video_url)
    else:
        return "No images available to create a video.", 404

if __name__ == '__main__':
    app.run(debug=True)
