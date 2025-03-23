//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/pages/StudentDashboardPage.jsx
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/StudentDashboardPage.css';

function StudentDashboardPage() {
  const [recommendedTopics, setRecommendedTopics] = useState([
    { id: 1, name: "Mechanics", progress: 65, priority: "high", aiConfidence: 92, aiRecommended: true },
    { id: 2, name: "Thermal Physics", progress: 40, priority: "medium", aiConfidence: 78, aiRecommended: false },
    { id: 3, name: "Waves", progress: 20, priority: "high", aiConfidence: 95, aiRecommended: true },
    { id: 4, name: "Electricity & Magnetism", progress: 75, priority: "low", aiConfidence: 65, aiRecommended: false },
    { id: 5, name: "Atomic & Nuclear Physics", progress: 30, priority: "medium", aiConfidence: 85, aiRecommended: true }
  ]);
  
  // Mock data for performance overview
  const [recentPracticeResults, setRecentPracticeResults] = useState([
    { id: 1, topic: "Motion", date: "2023-05-15", score: 85, timeSpent: "25 min" },
    { id: 2, topic: "Electricity", date: "2023-05-14", score: 72, timeSpent: "18 min" },
    { id: 3, topic: "Forces", date: "2023-05-12", score: 68, timeSpent: "30 min" }
  ]);
  
  // Mock data for skill mastery
  const [skillMastery, setSkillMastery] = useState([
    { id: 1, skill: "Kinematics", level: "Advanced", progress: 92 },
    { id: 2, skill: "Circular Motion", level: "Intermediate", progress: 75 },
    { id: 3, skill: "Thermodynamics", level: "Beginner", progress: 45 },
    { id: 4, skill: "Electric Circuits", level: "Intermediate", progress: 68 }
  ]);
  
  // Mock data for assessment scores
  const [recentAssessments, setRecentAssessments] = useState([
    { id: 1, name: "Mechanics Mid-Term", date: "2023-05-10", score: 88, improvement: 5 },
    { id: 2, name: "Waves & Optics Quiz", date: "2023-05-05", score: 75, improvement: 3 },
    { id: 3, name: "Electromagnetism Test", date: "2023-04-28", score: 82, improvement: 7 }
  ]);
  
  // Mock data for skill gaps
  const [skillGaps, setSkillGaps] = useState([
    { id: 1, skill: "Relativity", status: "critical", recommendedResource: "Relativity Physics Practice Set" },
    { id: 2, skill: "Electromagnetic Induction", status: "warning", recommendedResource: "Faraday's Law Workshop" },
    { id: 3, skill: "Projectile Motion", status: "moderate", recommendedResource: "Intro to Projectile Motion" }
  ]);
  
  // Mock data for progress history
  const [progressHistory, setProgressHistory] = useState([
    { month: "Jan", avgScore: 72 },
    { month: "Feb", avgScore: 75 },
    { month: "Mar", avgScore: 79 },
    { month: "Apr", avgScore: 82 },
    { month: "May", avgScore: 86 }
  ]);
  
  // Mock data for completed assessments
  const [completedAssessments, setCompletedAssessments] = useState([
    { id: 1, name: "Kinematics & Dynamics", attempts: 2, highestScore: 92, completedDate: "2023-04-15" },
    { id: 2, name: "Thermal Physics", attempts: 1, highestScore: 88, completedDate: "2023-03-22" },
    { id: 3, name: "Wave Phenomena", attempts: 3, highestScore: 79, completedDate: "2023-02-18" }
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
        { id: 1, name: "Mechanics", progress: 68, priority: "medium", aiConfidence: 86, aiRecommended: true },
        { id: 2, name: "Wave Phenomena", progress: 45, priority: "high", aiConfidence: 91, aiRecommended: true },
        { id: 3, name: "Thermodynamics", progress: 25, priority: "low", aiConfidence: 72, aiRecommended: false },
        { id: 4, name: "Electromagnetism", progress: 80, priority: "low", aiConfidence: 65, aiRecommended: false },
        { id: 5, name: "Nuclear Physics", progress: 35, priority: "medium", aiConfidence: 88, aiRecommended: true }
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
          <Link to="/student/assessment" className={`nav-item ${isActive('/student/assessment') || isActive('/student/practice') ? 'active' : ''}`}>
            <span className="nav-icon">📝</span>
            <span className="nav-label">Practice/Assessment</span>
          </Link>
        </div>
      </div>

      <div className="dashboard-header">
        <h1>Student Dashboard</h1>
        <p>Track your progress in IBDP Physics</p>
        <span className="welcome-message">Welcome back, Physics Student!</span>
      </div>

      <div className="dashboard-content">
        {/* Top Row - Performance + Skill Gap */}
        <div className="dashboard-row">
          {/* Performance Overview Section */}
          <div className="performance-overview-section">
            <div className="section-header">
              <h2>Performance Overview</h2>
            </div>
            
            <div className="performance-overview-grid">
              {/* Recent Practice Results */}
              <div className="performance-card">
                <h3>Recent Practice Results</h3>
                <div className="practice-results-list">
                  {recentPracticeResults.map(practice => (
                    <div key={practice.id} className="practice-result-item">
                      <div className="practice-topic">{practice.topic}</div>
                      <div className="practice-details">
                        <span className="practice-date">{practice.date}</span>
                        <span className="practice-score">Score: {practice.score}%</span>
                        <span className="practice-time">Time: {practice.timeSpent}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Skill Mastery Levels */}
              <div className="performance-card">
                <h3>Skill Mastery Levels</h3>
                <div className="skill-mastery-list">
                  {skillMastery.map(skill => (
                    <div key={skill.id} className="skill-mastery-item">
                      <div className="skill-info">
                        <span className="skill-name">{skill.skill}</span>
                        <span className={`skill-level ${skill.level.toLowerCase()}`}>{skill.level}</span>
                      </div>
                      <div className="skill-progress-bar">
                        <div className="skill-progress-fill" style={{ width: `${skill.progress}%` }}></div>
                      </div>
                      <span className="skill-progress-text">{skill.progress}%</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Recent Assessment Scores */}
              <div className="performance-card">
                <h3>Recent Assessment Scores</h3>
                <div className="assessment-scores-list">
                  {recentAssessments.map(assessment => (
                    <div key={assessment.id} className="assessment-score-item">
                      <div className="assessment-name">{assessment.name}</div>
                      <div className="assessment-details">
                        <span className="assessment-date">{assessment.date}</span>
                        <span className="assessment-score">Score: {assessment.score}%</span>
                        <span className="assessment-improvement">
                          <span className="improvement-indicator">↑</span> {assessment.improvement}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          {/* Skill Gap Identification Section */}
          <div className="skill-gap-section">
            <div className="section-header">
              <h2>Detailed Skill Gap Analysis</h2>
            </div>
            
            <p className="section-description">
              Focus on these areas to improve your IBDP Physics performance.
            </p>
            
            <div className="skill-gap-grid">
              {skillGaps.map(gap => (
                <div key={gap.id} className={`skill-gap-card status-${gap.status}`}>
                  <div className="skill-gap-header">
                    <h3 className="skill-gap-name">{gap.skill}</h3>
                    <span className={`skill-gap-status status-${gap.status}`}>
                      {gap.status === 'critical' ? '⚠️ Needs Work' : 
                      gap.status === 'warning' ? '⚠️ Improve' : '⚙️ Review'}
                    </span>
                  </div>
                  
                  <div className="skill-gap-resources">
                    <span className="resource-label">Recommended:</span>
                    <span className="resource-name">{gap.recommendedResource}</span>
                    <Link to="/student/assessment" className="resource-link">Practice Now</Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Middle Row - Progress History + Knowledge Map */}
        <div className="dashboard-row">
          {/* Progress Tracking & History Section */}
          <div className="progress-history-section">
            <div className="section-header">
              <h2>Progress Tracking & History</h2>
            </div>
            
            <div className="progress-history-grid">
              {/* Progress Chart */}
              <div className="progress-chart-card">
                <h3>Performance Over Time</h3>
                <div className="progress-chart">
                  {progressHistory.map((point, index) => (
                    <div key={index} className="chart-column">
                      <div className="chart-bar" style={{ height: `${point.avgScore}%` }}>
                        <span className="chart-value">{point.avgScore}%</span>
                      </div>
                      <span className="chart-label">{point.month}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Completed Assessments */}
              <div className="completed-assessments-card">
                <h3>Completed Assessments</h3>
                <div className="completed-assessments-list">
                  {completedAssessments.map(assessment => (
                    <div key={assessment.id} className="completed-assessment-item">
                      <div className="assessment-name">{assessment.name}</div>
                      <div className="assessment-details">
                        <span className="assessment-attempts">Attempts: {assessment.attempts}</span>
                        <span className="assessment-highest">Highest: {assessment.highestScore}%</span>
                        <span className="assessment-completed-date">Completed: {assessment.completedDate}</span>
                      </div>
                      <button className="review-assessment-btn">Review Results</button>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Learning Goals */}
              <div className="learning-goals-card">
                <h3>Learning Goals</h3>
                <div className="learning-goals-content">
                  <div className="active-goal">
                    <span className="goal-label">Active Goal:</span>
                    <span className="goal-title">Master Electromagnetism</span>
                    <div className="goal-progress-bar">
                      <div className="goal-progress-fill" style={{ width: '65%' }}></div>
                    </div>
                    <span className="goal-progress-text">65% Complete</span>
                  </div>
                  
                  <div className="completed-goals">
                    <span className="completed-goals-label">Completed Goals:</span>
                    <ul className="completed-goals-list">
                      <li>Complete Mechanics Fundamentals <span className="completion-date">Apr 10, 2023</span></li>
                      <li>Finish Waves & Optics <span className="completion-date">Mar 22, 2023</span></li>
                    </ul>
                  </div>
                  
                  <button className="set-new-goal-btn">Set New Goal</button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Knowledge Map Section */}
          <div className="knowledge-map-section">
            <div className="section-header">
              <h2>Your Physics Knowledge Map</h2>
              <div className="section-actions">
                <button onClick={refreshRecommendations} className="refresh-btn" disabled={loading}>
                  {loading ? 'Refreshing...' : 'Refresh Recommendations'}
                </button>
              </div>
            </div>

            <p className="section-description">
              Focus on these IBDP Physics topics to improve your skills - AI-powered recommendations highlighted
            </p>

            {loading ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>Analyzing your physics learning patterns...</p>
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
        </div>

        {/* Bottom Row - Learning Stats */}
        <div className="stats-section">
          <h3>Your Physics Learning Stats</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-number">{learningStats.modulesCompleted}</span>
              <span className="stat-label">Physics Modules Completed</span>
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