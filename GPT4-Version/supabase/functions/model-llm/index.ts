// Import the serve function from Supabase Edge Runtime
import { serve } from 'https://esm.sh/@supabase/functions-js/src/edge-runtime.d.ts';

// Create a new session for the 'gte-small' m
const model = new Supabase.ai.Session('gte-small');

// Define and export the service function
serve(async (req: Request) => {
  try {
    // Get the request parameters
    const params = new URL(req.url).searchParams;
    const input = params.get('input');

    // Check if input is present
    if (!input) {
      return new Response(JSON.stringify({ error: 'Input is required' }), {
        headers: { 'Content-Type': 'application/json' },
        status: 400,
      });
    }

    // Perform model inference with mean_pool and normalize options
    const output = await model.run(input, { mean_pool: true, normalize: true });

    // Return the inference result
    return new Response(JSON.stringify(output), {
      headers: {
        'Content-Type': 'application/json',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    // Handle errors
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { 'Content-Type': 'application/json' },
      status: 500,
    });
  }
});
