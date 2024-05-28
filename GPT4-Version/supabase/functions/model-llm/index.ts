// Assurez-vous que le modèle Mistral est téléchargé via Ollama

Deno.serve(async (req: Request) => {
  const params = new URL(req.url).searchParams;
  const prompt = params.get('prompt') ?? 'WHAT IS LOVE ';

  console.log(`Received prompt: ${prompt}`);

  try {
    // Appeler l'API Ollama pour générer du texte
    const response = await fetch('http://localhost:5000/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ model: 'mistral', prompt: prompt }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate text');
    }

    const data = await response.json();
    const generatedText = data.text;
    console.log(`Generated text: ${generatedText}`);

    return new Response(generatedText, {
      headers: { 'Content-Type': 'text/plain' },
    });
  } catch (error) {
    console.error('Error generating text:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { 'Content-Type': 'application/json' },
      status: 500,
    });
  }
});
