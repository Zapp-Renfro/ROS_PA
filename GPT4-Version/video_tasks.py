import boto3
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.editor import ImageClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip
from io import BytesIO
import numpy as np
import os
import logging
from PIL import Image, ImageDraw, ImageFont

AWS_ACCESS_KEY_ID = 'AKIAVRUVT3YMY5C23CNL'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = 'eu-west-1'


def text_to_speech(text, output_filename, voice_id='Justin'):
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


def create_text_frames(text, duration, fps, image_size, font_path, font_size=48, text_color=(255, 255, 255)):
    font = ImageFont.truetype(font_path, font_size)
    text_frames = []

    num_frames = int(duration * fps)
    fade_duration = 0.5  # duration of the fade effect in seconds
    fade_frames = int(fade_duration * fps)

    for i in range(num_frames):
        img = Image.new("RGBA", image_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 2)

        alpha = 255
        if i < fade_frames:
            alpha = int(255 * (i / fade_frames))  # Fade in
        elif i >= num_frames - fade_frames:
            alpha = int(255 * ((num_frames - i) / fade_frames))  # Fade out

        draw.text(position, text, font=font, fill=(text_color[0], text_color[1], text_color[2], alpha))
        text_frames.append(np.array(img))

    return text_frames

def create_video_with_text(images_data, output_video, prompts, fps=1, audio_path='static/music/relaxing-piano-201831.mp3', voice_id='Justin'):
    audio_clips = []
    video_clips = []
    audio_dir = 'static/audio'
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
    for audio_file in os.listdir(audio_dir):
        os.remove(os.path.join(audio_dir, audio_file))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Adjust the font path as needed

    for img_data, prompt in zip(images_data, prompts):
        audio_filename = os.path.join(audio_dir, f"{prompt[:10]}_audio.mp3")
        text_to_speech(prompt, audio_filename, voice_id)
        speech_clip = AudioFileClip(audio_filename)

        image = Image.open(img_data).convert('RGBA')
        img_array = np.array(image)
        img_clip = ImageClip(img_array).set_duration(speech_clip.duration)

        # Create text frames with fade in/out effect
        text_frames = create_text_frames(prompt, speech_clip.duration, fps, img_clip.size, font_path, font_size=48)
        text_clips = [ImageClip(img).set_duration(1 / fps) for img in text_frames]

        text_clip = concatenate_videoclips(text_clips, method="compose")

        # Composite the image clip with the text clip
        video = CompositeVideoClip([img_clip, text_clip.set_position('center')]).set_duration(speech_clip.duration)
        video = video.set_audio(speech_clip)

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
