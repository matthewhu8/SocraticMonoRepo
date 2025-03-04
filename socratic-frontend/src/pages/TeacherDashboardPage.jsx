//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/pages/TeacherDashboardPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/TeacherDashboardPage.css';

function TeacherDashboardPage() {
  return (
    <div className="teacher-dashboard-container">
      <div className="dashboard-header">
        <h1>Teacher Dashboard</h1>
        <p>Create and manage your educational content</p>
      </div>
      
      <div className="dashboard-content">
        <div className="action-cards">
          <Link to="/teachers/create-test" className="action-card">
            <div className="card-icon">📝</div>
            <div className="card-content">
              <h2>Create Test</h2>
              <p>Generate tests with custom questions and automatic grading</p>
            </div>
          </Link>
          
          <Link to="/teachers/create-learning-module" className="action-card">
            <div className="card-icon">📚</div>
            <div className="card-content">
              <h2>Create Learning Module</h2>
              <p>Design interactive learning modules with guided instruction</p>
            </div>
          </Link>
          
          <Link to="/teachers/create-practice-exam" className="action-card">
            <div className="card-icon">🧠</div>
            <div className="card-content">
              <h2>Create Practice Exam</h2>
              <p>Build practice exams with comprehensive feedback</p>
            </div>
          </Link>
        </div>

        <div className="stats-section">
          <h3>Quick Statistics</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-number">0</span>
              <span className="stat-label">Active Tests</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">0</span>
              <span className="stat-label">Learning Modules</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">0</span>
              <span className="stat-label">Student Submissions</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="dashboard-footer">
        <Link to="/" className="back-link">Back to Home</Link>
      </div>
    </div>
  );
}

export default TeacherDashboardPage;