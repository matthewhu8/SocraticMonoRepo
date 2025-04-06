//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/pages/HomePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/HomePage.css';

function HomePage() {
  return (
    <div className="home-container">
      <div className="home-header">
        <h1>Welcome to Socratic</h1>
        <p>An interactive learning platform for students and teachers</p>
      </div>
      
      <div className="dashboard-options">
        <Link to="/student/auth" className="dashboard-card">
          <div className="card-icon">👨‍🎓</div>
          <h2>Student Access</h2>
          <p>Sign in or create an account to access your tests, practice problems, and learning modules</p>
        </Link>
        
        <Link to="/teachers/auth" className="dashboard-card">
          <div className="card-icon">👩‍🏫</div>
          <h2>Teacher Access</h2>
          <p>Sign in or create an account to manage tests, learning modules, and practice exams</p>
        </Link>
      </div>
      
      <div className="home-footer">
        <p>Enhancing education through guided learning and exploration</p>
      </div>
    </div>
  );
}

export default HomePage;