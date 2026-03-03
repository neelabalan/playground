import React from "react";
import useNavigation from "../hooks/useNavigation";
import "./HomePage.css"; // Import the CSS file for styling

const HomePage = () => {
  const { navigate } = useNavigation();

  const handleSignIn = () => {
    navigate("/signin"); // Navigate to the sign-in page
  };

  return (
    <div className="home-container">
      <header className="home-header">
        <img
          src="https://www.reshot.com/preview-assets/icons/TRSZVWDKE5/writing-notes-TRSZVWDKE5.svg"
          alt="Notes App Logo"
          className="logo"
        />

        <h1>Welcome to Notes App</h1>
      </header>

      <main className="home-main">
        <section className="hero-section">
          <div className="hero-content">
            <h2>Organize Your Thoughts</h2>
            <p>
              Capture ideas, manage tasks, and collaborate—all in one place.
            </p>
            <button onClick={handleSignIn} className="sign-in-button">
              Get Started
            </button>
            <button onClick={() => navigate("/signup")} className="sign-in-button" style={{ marginLeft: "1rem", background: "transparent", border: "1px solid" }}>
              Sign Up
            </button>
          </div>
          <img
            src="https://i.postimg.cc/tgh3pghM/DALL-E-2024-10-05-10-23-20-A-digital-illustration-for-a-website-feature-section-titled-Easy-Note.webp"
            alt="Hero"
            className="hero-image"
          />
        </section>

        <section className="features-section">
          <h2>Features</h2>
          <div className="features">
            <div className="feature-item">
              <img
                src="https://i.postimg.cc/BvGFYGdc/DALL-E-2024-10-05-10-29-11-A-sleek-and-futuristic-digital-illustration-showing-an-innovative-PC-se.webp" 
                alt="Feature 1"
              />
              <h3>Easy Note-Taking</h3>
              <p>
                Quickly jot down notes and ideas with our user-friendly
                interface.
              </p>
            </div>
            <div className="feature-item">
              <img
                src="https://i.postimg.cc/mrxYv9F9/DALL-E-2024-10-05-10-23-56-A-digital-illustration-for-a-website-feature-section-titled-Organize-N.webp"
                alt="Feature 2"
              />
              <h3>Organize Notes</h3>
              <p>
                Sort and categorize your notes to keep everything neat and
                accessible.
              </p>
            </div>
            <div className="feature-item">
              <img
                src="https://i.postimg.cc/fTrjvpzB/DALL-E-2024-10-05-10-24-24-A-digital-illustration-for-a-website-feature-section-titled-Cloud-Sync.webp"
                alt="Feature 3"
              />
              <h3>Cloud Sync</h3>
              <p>Access your notes from anywhere, on any device.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="home-footer">
        <p>&copy; 2026 Notes App. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default HomePage;
