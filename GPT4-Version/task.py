import os
import base64
from io import BytesIO
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import logging
from supabase import create_client, Client

# Configure Supabase client
# Initialisation de Supabase
SUPABASE_URL = 'https://lpfjfbvhhckrnzdfezgd.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwZmpmYnZoaGNrcm56ZGZlemdkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTY2NTYyMzEsImV4cCI6MjAzMjIzMjIzMX0.xXvve7bQ0lSz38CT9s9iQF3VlPo-vKbCy5Vw3Zhl84c'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
HEADERS_LIST = [{"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}]

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def text_to_image(image_array, text, font_size=48):
    image = Image.fromarray(image_array)
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    max_width = image.width - 40
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if draw.textsize(test_line, font=font)[0] <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word + " "
    lines.append(line)

    y = (image.height - len(lines) * font_size) // 2
    for line in lines:
        draw.text(((image.width - draw.textsize(line, font=font)[0]) / 2, y), line, font=font, fill="white")
        y += font_size

    return np.array(image)

def create_video_with_text(images_data, output_video, prompts, fps=1, audio_path='static/music/relaxing-piano-201831.mp3', voice_id='Justin'):
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

        # Create a TextClip that displays text gradually using PIL
        def text_generator(txt, duration, img_size):
            try:
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                font = ImageFont.truetype(font_path, 24)
            except IOError:
                font = ImageFont.load_default()
            clip_duration = duration / len(txt.split())
            text_clips = []
            for i, word in enumerate(txt.split()):
                img_copy = Image.fromarray(img_with_text.copy())  # Ensure we're working with PIL.Image
                draw = ImageDraw.Draw(img_copy)
                draw.text((20, img_size[1] // 2), ' '.join(txt.split()[:i+1]), font=font, fill='white')
                text_clip = ImageClip(np.array(img_copy)).set_duration(clip_duration)
                text_clips.append(text_clip)
            return concatenate_videoclips(text_clips)

        txt_clip = text_generator(prompt, speech_clip.duration, img_clip.size)

        video = CompositeVideoClip([img_clip, txt_clip.set_position('center')]).set_audio(speech_clip)
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

def fetch_images(code):
    response = supabase.table('images').select('image_blob').eq('code', code).execute()
    images_data = []
    if response.data:
        for img in response.data:
            image_blob = img.get('image_blob')
            if image_blob:
                try:
                    images_data.append(BytesIO(base64.b64decode(image_blob)))
                    logging.info(f"Image retrieved for code {code}")
                except Exception as e:
                    logging.error(f"Failed to decode image for code {code}: {e}")
    return images_data
