import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/TeacherDashboardPage.css';

function TeacherDashboardPage() {
  // Mock student data - in a real app, this would come from an API
  const students = [
    { id: 1, name: "Sarah Johnson", progress: 75, completedTasks: 15, totalTasks: 20, image: "https://i.pravatar.cc/150?img=1" },
    { id: 2, name: "Michael Chen", progress: 60, completedTasks: 12, totalTasks: 20, image: "https://i.pravatar.cc/150?img=2" },
    { id: 3, name: "Emma Davis", progress: 90, completedTasks: 18, totalTasks: 20, image: "https://i.pravatar.cc/150?img=3" },
    { id: 4, name: "James Wilson", progress: 45, completedTasks: 9, totalTasks: 20, image: "https://i.pravatar.cc/150?img=4" },
    { id: 5, name: "Sofia Rodriguez", progress: 85, completedTasks: 17, totalTasks: 20, image: "https://i.pravatar.cc/150?img=5" },
    { id: 6, name: "Aiden Patel", progress: 70, completedTasks: 14, totalTasks: 20, image: "https://i.pravatar.cc/150?img=6" },
    { id: 7, name: "Isabella Kim", progress: 95, completedTasks: 19, totalTasks: 20, image: "https://i.pravatar.cc/150?img=7" },
    { id: 8, name: "Lucas Thompson", progress: 55, completedTasks: 11, totalTasks: 20, image: "https://i.pravatar.cc/150?img=8" },
    { id: 9, name: "Olivia Martinez", progress: 80, completedTasks: 16, totalTasks: 20, image: "https://i.pravatar.cc/150?img=9" },
    { id: 10, name: "Ethan Nguyen", progress: 65, completedTasks: 13, totalTasks: 20, image: "https://i.pravatar.cc/150?img=10" },
    { id: 11, name: "Ava Williams", progress: 88, completedTasks: 17, totalTasks: 20, image: "https://i.pravatar.cc/150?img=11" },
    { id: 12, name: "Noah Garcia", progress: 72, completedTasks: 14, totalTasks: 20, image: "https://i.pravatar.cc/150?img=12" },
    { id: 15, name: "Tank Bigsby", progress: 72, completedTasks: 14, totalTasks: 20, image: "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/4431611.png" }
  ];

  // Mock class insights data - would come from API in a real app
  const classInsights = [
    {
      type: "weak",
      title: "Kinematics Calculations",
      status: "Needs Review",
      details: "65% of students struggle with projectile motion calculations",
      recommendation: "Consider implementing a dedicated projectile motion mini-module"
    },
    {
      type: "strong",
      title: "Electrical Circuits",
      status: "Very Strong Performance",
      details: "90% of students show mastery in analyzing simple circuit configurations",
      recommendation: "Ready for advanced circuit analysis concepts"
    },
    {
      type: "weak",
      title: "Wave Problems",
      status: "Needs Attention",
      details: "Multiple students having difficulty translating wave equations to problem contexts",
      recommendation: "Provide additional examples with step-by-step wave problem breakdowns"
    }
  ];

  // Mock teaching suggestions based on data
  const teachingSuggestions = [
    {
      title: "Adjust Pacing for Mechanics",
      description: "Data suggests slowing down on projectile motion and providing more hands-on demonstrations",
      impact: "Could improve understanding for 8 struggling students"
    },
    {
      title: "Enrichment Opportunity: Electromagnetism",
      description: "Class shows strong understanding of basic circuits. Consider introducing electromagnetic induction.",
      impact: "Could challenge 10 high-performing students"
    }
  ];

  return (
    <div className="teacher-dashboard-container">
      <div className="dashboard-header">
        <h1>IBDP Physics Teacher Dashboard</h1>
        <p>Create and manage your physics educational content</p>
      </div>
      
      <div className="action-buttons">
        <Link to="/teachers/create-test" className="action-button">
          <div className="button-icon">📝</div>
          <h2>Create Physics Test</h2>
          <p>Generate physics tests with custom questions</p>
        </Link>
        
        <Link to="/teachers/create-learning-module" className="action-button">
          <div className="button-icon">📚</div>
          <h2>Create Physics Module</h2>
          <p>Design interactive physics learning modules</p>
        </Link>
        
        <Link to="/teachers/create-practice-exam" className="action-button">
          <div className="button-icon">🧠</div>
          <h2>Create Physics Practice Exam</h2>
          <p>Build IBDP-style physics practice exams with AI feedback</p>
        </Link>
      </div>

      <div className="dashboard-content">
        <div className="analytics-section full-width">
          <h2>Physics Class Insights</h2>
          <p className="section-description">
            Aggregated physics performance data showing common patterns and areas needing attention
          </p>
          
          <div className="insights-container">
            {classInsights.map((insight, index) => (
              <Link 
                key={index} 
                to={`/teachers/topic/${insight.title.toLowerCase().replace(/\s+/g, '-')}`} 
                className={`insight-card ${insight.type}`}
              >
                <div className="insight-header">
                  <h3>{insight.title}</h3>
                  <span className="status-badge">{insight.status}</span>
                </div>
                <div className="insight-details">
                  <p>{insight.details}</p>
                  <p className="insight-recommendation">{insight.recommendation}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="analytics-section full-width">
          <h2>Physics Teaching Recommendations</h2>
          <p className="section-description">
            Data-driven suggestions to improve physics class performance
          </p>
          
          <div className="suggestions-container">
            {teachingSuggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-card">
                <h3>{suggestion.title}</h3>
                <p className="suggestion-description">{suggestion.description}</p>
                <div className="suggestion-impact">
                  <span className="impact-label">Potential Impact:</span>
                  <span className="impact-value">{suggestion.impact}</span>
                </div>
                <button className="implement-button">Implement</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="active-content-section">
        <h2>Active Physics Content</h2>
        <div className="content-grid">
          <div className="content-column">
            <h3>Active Tests <span className="count">(3)</span></h3>
            <ul className="content-list">
              <li className="content-item">
                <span className="content-title">Mechanics Quiz</span>
                <span className="content-students">24 students</span>
              </li>
              <li className="content-item">
                <span className="content-title">Electricity & Magnetism Test</span>
                <span className="content-students">18 students</span>
              </li>
              <li className="content-item">
                <span className="content-title">Waves & Optics Final</span>
                <span className="content-students">32 students</span>
              </li>
            </ul>
          </div>

          <div className="content-column">
            <h3>Learning Modules <span className="count">(2)</span></h3>
            <ul className="content-list">
              <li className="content-item">
                <span className="content-title">Kinematics Fundamentals</span>
                <span className="content-students">28 students</span>
              </li>
              <li className="content-item">
                <span className="content-title">Atomic & Nuclear Physics</span>
                <span className="content-students">22 students</span>
              </li>
            </ul>
          </div>

          <div className="content-column">
            <h3>Practice Exams <span className="count">(2)</span></h3>
            <ul className="content-list">
              <li className="content-item">
                <span className="content-title">IBDP Physics Paper 1 Practice</span>
                <span className="content-students">45 students</span>
              </li>
              <li className="content-item">
                <span className="content-title">IBDP Physics Paper 2 Practice</span>
                <span className="content-students">38 students</span>
              </li>
            </ul>
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