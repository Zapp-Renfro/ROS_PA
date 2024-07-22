import { useState } from 'react';
import axios from 'axios';
import Link from 'next/link';

export default function Start() {
  const [promptStart, setPromptStart] = useState('');
  const [prompt, setPrompt] = useState('');
  const [modelApi, setModelApi] = useState('');
  const [response, setResponse] = useState('');
  const [userText, setUserText] = useState('');
  const [models, setModels] = useState([]);

  // Fetch models from backend on component mount
  useEffect(() => {
    axios.get('/api/models')  // Assumes an endpoint to get models
      .then(res => setModels(res.data))
      .catch(err => console.error(err));
  }, []);

  const handleGenerateText = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('/generate_text', { prompt_start: promptStart, prompt, model_api: modelApi });
      setResponse(res.data.response);
    } catch (error) {
      console.error(error);
    }
  };

  const handleUseText = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('/use_text', { prompt2: userText });
      setResponse(res.data.response);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <header className="w3-top">
        <div className="w3-bar" id="myNavbar">
          <Link href="/">
            <a className="w3-bar-item w3-button">HOME</a>
          </Link>
          <a href="#about" className="w3-bar-item w3-button w3-hide-small">
            <i className="fa fa-user"></i> Video creation
          </a>
          <Link href="/logout">
            <a className="w3-bar-item w3-button w3-hide-small w3-right w3-hover-red">Logout</a>
          </Link>
          <Link href="/login">
            <a className="w3-bar-item w3-button w3-hide-small w3-right w3-hover-red">Login</a>
          </Link>
          <Link href="/signup">
            <a className="w3-bar-item w3-button w3-hide-small w3-right w3-hover-red">Signup</a>
          </Link>
        </div>
      </header>
      <div className="bgimg-1 w3-display-container w3-opacity-min" id="home">
        <div className="w3-display-middle" style={{ whiteSpace: 'nowrap' }}>
          <span className="w3-center w3-padding-large w3-black w3-xlarge w3-wide w3-animate-opacity">
            PA <span className="w3-hide-small">ROS</span> WEBSITE
          </span>
        </div>
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
              <input type="text" id="prompt" name="prompt" required value={prompt} onChange={(e) => setPrompt(e.target.value)} />
              <br />
              <label htmlFor="model_api">Model:</label>
              <select id="model_api" name="model_api" required value={modelApi} onChange={(e) => setModelApi(e.target.value)}>
                {models.map((model) => (
                  <option key={model.url} value={model.url}>{model.name}</option>
                ))}
              </select>
              <br />
              <input type="submit" value="Generate text" />
            </form>
          </div>
          <div className="container">
            <form onSubmit={handleUseText}>
              <label htmlFor="prompt2">I already have a script.</label>
              <input type="text" id="prompt2" name="prompt2" required value={userText} onChange={(e) => setUserText(e.target.value)} />
              <input type="submit" value="Use" />
            </form>
          </div>
        </div>
        {response && (
          <div className="response-container">
            <h3>Response:</h3>
            <p>{response}</p>
          </div>
        )}
      </div>
      <footer className="w3-center w3-black w3-padding-64 w3-opacity w3-hover-opacity-off">
        <Link href="#home">
          <a className="w3-button w3-light-grey">
            <i className="fa fa-arrow-up w3-margin-right"></i>To the top
          </a>
        </Link>
        <div className="w3-xlarge w3-section">
          <i className="fa fa-facebook-official w3-hover-opacity"></i>
          <i className="fa fa-instagram w3-hover-opacity"></i>
          <i className="fa fa-snapchat w3-hover-opacity"></i>
          <i className="fa fa-pinterest-p w3-hover-opacity"></i>
          <i className="fa fa-twitter w3-hover-opacity"></i>
          <i className="fa fa-linkedin w3-hover-opacity"></i>
        </div>
        <p>
          Powered by <a href="https://www.w3schools.com/w3css/default.asp" title="W3.CSS" target="_blank" className="w3-hover-text-green">w3.css</a>
        </p>
      </footer>
    </div>
  );
}
