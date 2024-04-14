import torch
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", safety_checker=None)
# pipe = pipe.to("cuda")
pipe.enable_sequential_cpu_offload()
pipe.enable_attention_slicing("max")

prompt = "In the morning light, The sun rises with all its might. Birds chirp and sing their tune, As the world begins anew. The air is crisp and fresh, As the breeze carries scents of blooming flowers. The sky is a canvas of colors, As the sun paints its masterful work. The trees sway in the gentle breeze, As the leaves rustle with ease. Nature's beauty surrounds us all, And we feel alive in this moment's sweetness. "
image = pipe(prompt).images[0]

image.save("astronaut_rides_horse.png")