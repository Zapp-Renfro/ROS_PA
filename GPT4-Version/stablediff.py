import torch
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", safety_checker=None)
# pipe = pipe.to("cuda")
pipe.enable_sequential_cpu_offload()
pipe.enable_attention_slicing("max")

prompt = "fais mois Velaris du roman acotar"
image = pipe(prompt).images[0]

image.save("velaris.png")