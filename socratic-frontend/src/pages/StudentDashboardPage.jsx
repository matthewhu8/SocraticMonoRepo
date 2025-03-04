//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/pages/StudentDashboardPage.jsx
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/StudentDashboardPage.css';

function StudentDashboardPage() {
  const [recommendedTopics, setRecommendedTopics] = useState([
    { id: 1, name: "Algebra", progress: 65, priority: "high", aiConfidence: 92, aiRecommended: true },
    { id: 2, name: "Geometry", progress: 40, priority: "medium", aiConfidence: 78, aiRecommended: false },
    { id: 3, name: "Calculus", progress: 20, priority: "high", aiConfidence: 95, aiRecommended: true },
    { id: 4, name: "Physics", progress: 75, priority: "low", aiConfidence: 65, aiRecommended: false },
    { id: 5, name: "Chemistry", progress: 30, priority: "medium", aiConfidence: 85, aiRecommended: true }
  ]);

  const learningStats = {
    modulesCompleted: 12,
    averageScore: "86%",
    daysStreak: 24
  };

  const [loading, setLoading] = useState(false);
  const location = useLocation();

  const refreshRecommendations = () => {
    setLoading(true);
    setTimeout(() => {
      const refreshedTopics = [
        { id: 1, name: "Algebra", progress: 68, priority: "medium", aiConfidence: 86, aiRecommended: true },
        { id: 2, name: "Geometry", progress: 45, priority: "high", aiConfidence: 91, aiRecommended: true },
        { id: 3, name: "Calculus", progress: 25, priority: "low", aiConfidence: 72, aiRecommended: false },
        { id: 4, name: "Physics", progress: 80, priority: "low", aiConfidence: 65, aiRecommended: false },
        { id: 5, name: "Chemistry", progress: 35, priority: "medium", aiConfidence: 88, aiRecommended: true }
      ];
      setRecommendedTopics(refreshedTopics);
      setLoading(false);
    }, 1500);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="student-dashboard-container">
      <div className="sticky-nav">
        <div className="nav-container">
          <Link to="/student/learning-modules" className={`nav-item ${isActive('/student/learning-modules') ? 'active' : ''}`}>
            <span className="nav-icon">📚</span>
            <span className="nav-label">Learning Modules</span>
          </Link>
          <Link to="/student/practice" className={`nav-item ${isActive('/student/practice') ? 'active' : ''}`}>
            <span className="nav-icon">🏋️‍♂️</span>
            <span className="nav-label">Practice</span>
          </Link>
          <Link to="/student/assessment" className={`nav-item ${isActive('/student/assessment') ? 'active' : ''}`}>
            <span className="nav-icon">📝</span>
            <span className="nav-label">Assessment</span>
          </Link>
        </div>
      </div>

      <div className="dashboard-header">
        <h1>Student Dashboard</h1>
        <p>Track your progress and continue your learning journey</p>
        <span className="welcome-message">Welcome back, Student!</span>
      </div>

      <div className="dashboard-content">
        <div className="knowledge-map-section">
          <div className="section-header">
            <h2>Your Knowledge Map</h2>
            <div className="section-actions">
              <button onClick={refreshRecommendations} className="refresh-btn" disabled={loading}>
                {loading ? 'Refreshing...' : 'Refresh Recommendations'}
              </button>
            </div>
          </div>

          <p className="section-description">
            Focus on these topics to improve your skills - AI-powered recommendations highlighted with 👨‍💻
          </p>

          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Analyzing your learning patterns...</p>
            </div>
          ) : (
            <div className="knowledge-map">
              {recommendedTopics.map(topic => (
                <div key={topic.id} className={`knowledge-node priority-${topic.priority} ${topic.aiRecommended ? 'ai-recommended' : ''}`} style={{ '--progress': `${topic.progress}%` }}>
                  <div className="topic-progress">
                    <div className="progress-bar">
                      <div className="progress-fill"></div>
                    </div>
                    <span className="progress-text">{topic.progress}%</span>
                  </div>
                  <div className="topic-name">{topic.name}</div>
                  {topic.aiRecommended && <div className="ai-confidence">AI: {topic.aiConfidence}%</div>}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="stats-section">
          <h3>Your Learning Stats</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-number">{learningStats.modulesCompleted}</span>
              <span className="stat-label">Modules Completed</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">{learningStats.averageScore}</span>
              <span className="stat-label">Average Score</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">{learningStats.daysStreak}</span>
              <span className="stat-label">Days Streak</span>
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

export default StudentDashboardPage;