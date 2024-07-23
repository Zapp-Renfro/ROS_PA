import React from 'react';
import styled from 'styled-components';
import Link from 'next/link';

const Navbar = styled.div`
  position: fixed;
  width: 100%;
  top: 0;
  z-index: 1;
  background-color: #fff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

const NavbarLink = styled.a`
  padding: 10px;
  text-decoration: none;
  color: #333;
  &:hover {
    background-color: #ddd;
  }
`;

const HeroSection = styled.div`
  height: 100vh;
  background-image: url('../../../../GPT4-Version/static/images/fond_index.png');
  background-attachment: fixed;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const HeroText = styled.div`
  text-align: center;
  padding: 20px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 2em;
`;

const Container = styled.div`
  max-width: 800px;
  margin: auto;
  padding: 20px;
`;

const FormContainer = styled.div`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 40px;
  margin: 20px auto;
  text-align: center;
`;

const StyledForm = styled.form`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const StyledInput = styled.input`
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 5px;
  border: 1px solid #ccc;
  width: 100%;
  box-sizing: border-box;
`;

const SubmitButton = styled.input`
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  &:hover {
    background-color: #0056b3;
  }
`;

const Footer = styled.footer`
  text-align: center;
  padding: 64px;
  background-color: #000;
  color: white;
`;

const Start = ({ isAuthenticated, userEmail, models }) => (
  <div>
    <Navbar>
      <Link href="#home" passHref>
        <NavbarLink>HOME</NavbarLink>
      </Link>
      <Link href="#about" passHref>
        <NavbarLink>Video creation</NavbarLink>
      </Link>
      {isAuthenticated ? (
        <>
          <Link href="#" passHref>
            <NavbarLink>{userEmail}</NavbarLink>
          </Link>
          <Link href="/logout" passHref>
            <NavbarLink>Logout</NavbarLink>
          </Link>
        </>
      ) : (
        <>
          <Link href="/login" passHref>
            <NavbarLink>Login</NavbarLink>
          </Link>
          <Link href="/signup" passHref>
            <NavbarLink>Signup</NavbarLink>
          </Link>
        </>
      )}
    </Navbar>

    <HeroSection id="home">
      <HeroText>PAROS WEBSITE</HeroText>
    </HeroSection>

    <Container id="about">
      <h3 className="w3-center">Text Generator</h3>
      <p className="w3-center"><em>Enter your prompt here.</em></p>

      <div className="boxes-container">
        <FormContainer>
          {isAuthenticated ? (
            <StyledForm action="/generate_text" method="post">
              <label htmlFor="prompt_start">Choose a prompt start:</label>
              <select id="prompt_start" name="prompt_start">
                <option value="make me">Make me</option>
                <option value="talk about">Talk about</option>
              </select>

              <br />
              <label htmlFor="prompt">Prompt:</label>
              <StyledInput type="text" id="prompt" name="prompt" required />
              <select id="model_api" name="model_api" required>
                {models.map((model) => (
                  <option key={model.url} value={model.url}>{model.name}</option>
                ))}
              </select>
              <SubmitButton type="submit" value="Generate text" />
            </StyledForm>
          ) : (
            <p className="w3-center"><em>Please sign in to use the text generation tool.</em></p>
          )}
        </FormContainer>

        <FormContainer>
          {isAuthenticated ? (
            <StyledForm action="/use_text" method="post">
              <label htmlFor="prompt2">I already have a script.</label>
              <StyledInput type="text" id="prompt2" name="prompt2" required />
              <SubmitButton type="submit" value="Use" />
            </StyledForm>
          ) : (
            <p className="w3-center"><em>Please sign in to paste your own text here.</em></p>
          )}
        </FormContainer>
      </div>
    </Container>

    <Footer>
      <a href="#home" className="w3-button w3-light-grey">
        <i className="fa fa-arrow-up w3-margin-right"></i>To the top
      </a>
      <div className="w3-xlarge w3-section">
        <i className="fa fa-facebook-official w3-hover-opacity"></i>
        <i className="fa fa-instagram w3-hover-opacity"></i>
        <i className="fa fa-snapchat w3-hover-opacity"></i>
        <i className="fa fa-pinterest-p w3-hover-opacity"></i>
        <i className="fa fa-twitter w3-hover-opacity"></i>
        <i className="fa fa-linkedin w3-hover-opacity"></i>
      </div>
      <p>Powered by <a href="https://www.w3schools.com/w3css/default.asp" title="W3.CSS" target="_blank" rel="noopener noreferrer" className="w3-hover-text-green">w3.css</a></p>
    </Footer>
  </div>
);

export default Start;
