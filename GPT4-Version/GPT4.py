from gpt4all import GPT4All
model = GPT4All(model_name='orca-mini-3b-gguf2-q4_0.gguf')
with model.chat_session():
    response1 = model.generate(prompt='tell me a short story of a dragon king', temp=0)
    print(model.current_chat_session)