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
        <Link to="/student" className="dashboard-card">
          <div className="card-icon">👨‍🎓</div>
          <h2>Student Dashboard</h2>
          <p>Access your tests, practice problems, and learning modules</p>
        </Link>
        
        <Link to="/teachers" className="dashboard-card">
          <div className="card-icon">👩‍🏫</div>
          <h2>Teacher Dashboard</h2>
          <p>Create and manage tests, learning modules, and practice exams</p>
        </Link>
      </div>
      
      <div className="home-footer">
        <p>Enhancing education through guided learning and exploration</p>
      </div>
    </div>
  );
}

export default HomePage;