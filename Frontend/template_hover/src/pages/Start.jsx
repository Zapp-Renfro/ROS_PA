import React, { useState } from 'react';
import { FiArrowRight } from "react-icons/fi";
import { MaxWidthWrapper } from "@/components/utils/MaxWidthWrapper";
import { motion } from "framer-motion";
import { SplashButton } from "@/components/buttons/SplashButton";
import { GhostButton } from "@/components/buttons/GhostButton";
import { GlowingChip } from "@/components/utils/GlowingChip";

const Start = () => {
  const [prompt, setPrompt] = useState('');
  const [promptStart, setPromptStart] = useState('make me');
  const [prompt2, setPrompt2] = useState('');
  const [modelApi, setModelApi] = useState('');

  const handleGenerateText = async (e) => {
    e.preventDefault();
    // Envoyer les données au serveur pour générer du texte
    const response = await fetch('/generate_text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt_start: promptStart, prompt, model_api: modelApi }),
    });
    const data = await response.json();
    // Traitez les données de réponse si nécessaire
    console.log(data);
  };

  const handleUseText = async (e) => {
    e.preventDefault();
    // Envoyer les données au serveur pour utiliser du texte existant
    const response = await fetch('/use_text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt2 }),
    });
    const data = await response.json();
    // Traitez les données de réponse si nécessaire
    console.log(data);
  };

  return (
    <MaxWidthWrapper className="relative z-20 flex flex-col items-center justify-center pb-12 pt-24 md:pb-36 md:pt-36">
      <motion.div
        initial={{ y: 25, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1.25, ease: "easeInOut" }}
        className="relative mb-6"
      >
        <GlowingChip>Welcome to Start Page 🚀</GlowingChip>
      </motion.div>
      <motion.h1
        initial={{ y: 25, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1.25, delay: 0.25, ease: "easeInOut" }}
        className="mb-3 text-center text-4xl font-extrabold leading-tight text-zinc-50 sm:text-5xl sm:leading-tight md:text-6xl md:leading-tight lg:text-7xl lg:leading-tight"
      >
        Get Started with Your New Journey
      </motion.h1>
      <motion.p
        initial={{ y: 25, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1.25, delay: 0.5, ease: "easeInOut" }}
        className="mb-9 max-w-2xl text-center text-lg text-zinc-400 sm:text-xl md:text-2xl"
      >
        Explore the features, benefits, and possibilities of our platform. Let's create something amazing together.
      </motion.p>
      <motion.div
        initial={{ y: 25, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1.25, delay: 0.75, ease: "easeInOut" }}
        className="flex flex-col items-center gap-4 sm:flex-row"
      >
        <SplashButton className="flex items-center gap-2 px-6 py-3 text-xl font-semibold text-white bg-green-600 rounded-lg shadow-lg hover:bg-green-700">
          Get Started
          <FiArrowRight />
        </SplashButton>
        <GhostButton
          onClick={() => alert("Learn more clicked!")}
          className="flex items-center gap-2 px-6 py-3 text-xl font-semibold text-green-600 bg-white border-2 border-green-600 rounded-lg shadow-lg hover:bg-green-100"
        >
          Learn More
        </GhostButton>
      </motion.div>
      <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
        <FeatureCard
          icon={<FiArrowRight size={30} />}
          title="Feature One"
          description="Detailed description of feature one."
        />
        <FeatureCard
          icon={<FiArrowRight size={30} />}
          title="Feature Two"
          description="Detailed description of feature two."
        />
        <FeatureCard
          icon={<FiArrowRight size={30} />}
          title="Feature Three"
          description="Detailed description of feature three."
        />
      </div>
      <div className="w3-content w3-container w3-padding-64" id="about">
        <h3 className="w3-center">Text Generator</h3>
        <p className="w3-center"><em>Enter your prompt here.</em></p>
        <div className="boxes-container">
          <div className="container">
            <form onSubmit={handleGenerateText}>
              <label htmlFor="prompt_start">Choose a prompt start:</label>
              <select id="prompt_start" name="prompt_start" value={promptStart} onChange={(e) => setPromptStart(e.target.value)}>
                <option value="make me">Make me</option>
                <option value="talk about">Talk about</option>
              </select>
              <br />
              <label htmlFor="prompt">Prompt:</label>
              <input type="text" id="prompt" name="prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} required />
              <br />
              <label htmlFor="model_api">Choose a model:</label>
              <select id="model_api" name="model_api" value={modelApi} onChange={(e) => setModelApi(e.target.value)} required>
                {/* Remplacer par les modèles disponibles */}
                <option value="model1">Model 1</option>
                <option value="model2">Model 2</option>
              </select>
              <br />
              <input type="submit" value="Generate text" />
            </form>
          </div>
          <div className="container">
            <form onSubmit={handleUseText}>
              <label htmlFor="prompt2">I already have a script.</label>
              <input type="text" id="prompt2" name="prompt2" value={prompt2} onChange={(e) => setPrompt2(e.target.value)} required />
              <input type="submit" value="Use" />
            </form>
          </div>
        </div>
      </div>
    </MaxWidthWrapper>
  );
};

const FeatureCard = ({ icon, title, description }) => (
  <div className="p-6 bg-white rounded-lg shadow-md">
    <div className="flex items-center justify-center w-12 h-12 mb-4 bg-green-100 rounded-full">
      {icon}
    </div>
    <h3 className="mb-2 text-2xl font-bold text-zinc-800">{title}</h3>
    <p className="text-zinc-600">{description}</p>
  </div>
);

export default Start;
