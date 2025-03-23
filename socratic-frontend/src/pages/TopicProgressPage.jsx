import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import '../styles/TopicProgressPage.css';

function TopicProgressPage() {
  const { topicId, topicName } = useParams();
  const [students, setStudents] = useState([]);
  const [topic, setTopic] = useState(null);
  const [loading, setLoading] = useState(true);

  // Mock data - in a real app, this would come from an API
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      const mockTopic = getMockTopic(topicName || topicId);
      setTopic(mockTopic);
      setStudents(mockTopic.studentProgress);
      setLoading(false);
    }, 500);
  }, [topicId, topicName]);

  // Helper function to get mock data
  const getMockTopic = (identifier) => {
    const topics = {
      'fractions': {
        id: 'fractions',
        name: 'Fraction Operations',
        description: 'Addition, subtraction, multiplication, and division of fractions',
        status: 'Needs Review',
        overallProgress: 65,
        studentProgress: [
          { id: 1, name: "Sarah Johnson", mastery: 55, image: "https://i.pravatar.cc/150?img=1", strengths: "Multiplication", weaknesses: "Addition and subtraction" },
          { id: 2, name: "Michael Chen", mastery: 48, image: "https://i.pravatar.cc/150?img=2", strengths: "Understanding concepts", weaknesses: "Complex operations" },
          { id: 3, name: "Emma Davis", mastery: 92, image: "https://i.pravatar.cc/150?img=3", strengths: "All operations", weaknesses: "None significant" },
          { id: 4, name: "James Wilson", mastery: 38, image: "https://i.pravatar.cc/150?img=4", strengths: "Basic concepts", weaknesses: "Most operations" },
          { id: 5, name: "Sofia Rodriguez", mastery: 78, image: "https://i.pravatar.cc/150?img=5", strengths: "Addition, division", weaknesses: "Subtraction" },
          { id: 6, name: "Aiden Patel", mastery: 60, image: "https://i.pravatar.cc/150?img=6", strengths: "Visualization", weaknesses: "Multi-step problems" },
          { id: 7, name: "Isabella Kim", mastery: 95, image: "https://i.pravatar.cc/150?img=7", strengths: "All operations", weaknesses: "None" },
          { id: 8, name: "Lucas Thompson", mastery: 42, image: "https://i.pravatar.cc/150?img=8", strengths: "Simple problems", weaknesses: "Complex operations" },
          { id: 9, name: "Olivia Martinez", mastery: 72, image: "https://i.pravatar.cc/150?img=9", strengths: "Understanding concepts", weaknesses: "Application" },
          { id: 10, name: "Ethan Nguyen", mastery: 58, image: "https://i.pravatar.cc/150?img=10", strengths: "Division", weaknesses: "Addition, Subtraction" },
          { id: 11, name: "Ava Williams", mastery: 82, image: "https://i.pravatar.cc/150?img=11", strengths: "Most operations", weaknesses: "Complex problems" },
          { id: 12, name: "Noah Garcia", mastery: 65, image: "https://i.pravatar.cc/150?img=12", strengths: "Basic operations", weaknesses: "Word problems" }
        ],
        recommendedActivities: [
          "Fraction Manipulatives: Use virtual fraction tiles for visual learning",
          "Guided Practice: Step-by-step walkthrough of fraction operations",
          "Interactive Games: Fractions Dash to reinforce addition and subtraction",
          "Real-world Applications: Recipe conversion problems"
        ]
      },
      'geometry': {
        id: 'geometry',
        name: 'Geometric Shapes',
        description: 'Identifying and analyzing properties of two and three-dimensional shapes',
        status: 'Strong Performance',
        overallProgress: 90,
        studentProgress: [
          { id: 1, name: "Sarah Johnson", mastery: 88, image: "https://i.pravatar.cc/150?img=1", strengths: "2D shapes", weaknesses: "3D calculations" },
          { id: 2, name: "Michael Chen", mastery: 95, image: "https://i.pravatar.cc/150?img=2", strengths: "All concepts", weaknesses: "None" },
          { id: 3, name: "Emma Davis", mastery: 97, image: "https://i.pravatar.cc/150?img=3", strengths: "All concepts", weaknesses: "None" },
          { id: 4, name: "James Wilson", mastery: 78, image: "https://i.pravatar.cc/150?img=4", strengths: "Basic shapes", weaknesses: "Complex properties" },
          { id: 5, name: "Sofia Rodriguez", mastery: 92, image: "https://i.pravatar.cc/150?img=5", strengths: "Properties, calculations", weaknesses: "None significant" },
          { id: 6, name: "Aiden Patel", mastery: 89, image: "https://i.pravatar.cc/150?img=6", strengths: "Most concepts", weaknesses: "Advanced problems" },
          { id: 7, name: "Isabella Kim", mastery: 98, image: "https://i.pravatar.cc/150?img=7", strengths: "All concepts", weaknesses: "None" },
          { id: 8, name: "Lucas Thompson", mastery: 83, image: "https://i.pravatar.cc/150?img=8", strengths: "Basic properties", weaknesses: "Application" },
          { id: 9, name: "Olivia Martinez", mastery: 94, image: "https://i.pravatar.cc/150?img=9", strengths: "All concepts", weaknesses: "None significant" },
          { id: 10, name: "Ethan Nguyen", mastery: 87, image: "https://i.pravatar.cc/150?img=10", strengths: "Shape properties", weaknesses: "Complex calculations" },
          { id: 11, name: "Ava Williams", mastery: 91, image: "https://i.pravatar.cc/150?img=11", strengths: "Most concepts", weaknesses: "None significant" },
          { id: 12, name: "Noah Garcia", mastery: 88, image: "https://i.pravatar.cc/150?img=12", strengths: "2D and 3D shapes", weaknesses: "Some calculations" }
        ],
        recommendedActivities: [
          "Advanced Geometry: Introduction to coordinate geometry",
          "Enrichment: 3D modeling projects",
          "Challenge Problems: Higher-order thinking geometry puzzles",
          "Independent Study: Exploration of geometric principles in architecture"
        ]
      },
      'word-problems': {
        id: 'word-problems',
        name: 'Word Problems',
        description: 'Translating real-world situations into mathematical equations',
        status: 'Needs Attention',
        overallProgress: 62,
        studentProgress: [
          { id: 1, name: "Sarah Johnson", mastery: 68, image: "https://i.pravatar.cc/150?img=1", strengths: "Single-step problems", weaknesses: "Multi-step problems" },
          { id: 2, name: "Michael Chen", mastery: 55, image: "https://i.pravatar.cc/150?img=2", strengths: "Number problems", weaknesses: "Rate and ratio problems" },
          { id: 3, name: "Emma Davis", mastery: 85, image: "https://i.pravatar.cc/150?img=3", strengths: "Most problem types", weaknesses: "Complex scenarios" },
          { id: 4, name: "James Wilson", mastery: 42, image: "https://i.pravatar.cc/150?img=4", strengths: "Simple problems", weaknesses: "Translation to equations" },
          { id: 5, name: "Sofia Rodriguez", mastery: 72, image: "https://i.pravatar.cc/150?img=5", strengths: "Understanding scenarios", weaknesses: "Setting up equations" },
          { id: 6, name: "Aiden Patel", mastery: 58, image: "https://i.pravatar.cc/150?img=6", strengths: "Basic problems", weaknesses: "Multi-step scenarios" },
          { id: 7, name: "Isabella Kim", mastery: 90, image: "https://i.pravatar.cc/150?img=7", strengths: "All problem types", weaknesses: "None significant" },
          { id: 8, name: "Lucas Thompson", mastery: 48, image: "https://i.pravatar.cc/150?img=8", strengths: "Simple scenarios", weaknesses: "Translation to math" },
          { id: 9, name: "Olivia Martinez", mastery: 65, image: "https://i.pravatar.cc/150?img=9", strengths: "Understanding problems", weaknesses: "Complex setups" },
          { id: 10, name: "Ethan Nguyen", mastery: 52, image: "https://i.pravatar.cc/150?img=10", strengths: "Basic scenarios", weaknesses: "Multi-step problems" },
          { id: 11, name: "Ava Williams", mastery: 78, image: "https://i.pravatar.cc/150?img=11", strengths: "Most problem types", weaknesses: "Some complex scenarios" },
          { id: 12, name: "Noah Garcia", mastery: 60, image: "https://i.pravatar.cc/150?img=12", strengths: "Understanding scenarios", weaknesses: "Setting up equations" }
        ],
        recommendedActivities: [
          "Problem Solving Framework: Teach the 5-step approach to word problems",
          "Visualization Techniques: Diagram drawing strategies",
          "Guided Practice: Step-by-step breakdowns with varied problem types",
          "Real-world Connections: Problems based on student interests"
        ]
      }
    };

    // If no specific identifier or not found, return the first topic
    if (!identifier || !topics[identifier.toLowerCase()]) {
      return topics.fractions;
    }

    return topics[identifier.toLowerCase()];
  };

  const getMasteryColorClass = (mastery) => {
    if (mastery >= 80) return 'mastery-high';
    if (mastery >= 60) return 'mastery-medium';
    return 'mastery-low';
  };

  if (loading) {
    return <div className="loading">Loading topic data...</div>;
  }

  return (
    <div className="topic-progress-container">
      <div className="topic-header">
        <div className="topic-title-section">
          <Link to="/teachers" className="back-button">
            ← Back to Dashboard
          </Link>
          <h1>{topic.name}</h1>
          <p className="topic-description">{topic.description}</p>
        </div>
        
        <div className="topic-summary">
          <div className="summary-box">
            <span className="summary-label">Overall Mastery</span>
            <div className="summary-progress-container">
              <div 
                className={`summary-progress-bar ${getMasteryColorClass(topic.overallProgress)}`} 
                style={{ width: `${topic.overallProgress}%` }}
              ></div>
            </div>
            <span className="summary-percentage">{topic.overallProgress}%</span>
          </div>
          
          <div className="summary-box">
            <span className="summary-label">Status</span>
            <span className={`status-tag ${topic.status === 'Strong Performance' ? 'status-strong' : 'status-needs-work'}`}>
              {topic.status}
            </span>
          </div>
        </div>
      </div>
      
      <div className="topic-content">
        <div className="students-progress-section">
          <h2>Student Mastery Levels</h2>
          <div className="students-mastery-grid">
            {students.map(student => (
              <div key={student.id} className="student-mastery-card">
                <div className="student-mastery-header">
                  <div className="student-info">
                    <img src={student.image} alt={student.name} className="student-image" />
                    <h3>{student.name}</h3>
                  </div>
                  <span className="mastery-percentage">{student.mastery}%</span>
                </div>
                
                <div className="mastery-progress-container">
                  <div 
                    className={`mastery-progress-bar ${getMasteryColorClass(student.mastery)}`} 
                    style={{ width: `${student.mastery}%` }}
                  ></div>
                </div>
                
                <div className="student-mastery-details">
                  <div className="mastery-detail">
                    <span className="detail-label">Strengths:</span>
                    <span className="detail-value">{student.strengths}</span>
                  </div>
                  <div className="mastery-detail">
                    <span className="detail-label">Areas for Growth:</span>
                    <span className="detail-value">{student.weaknesses}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="recommendations-section">
          <h2>Recommended Activities</h2>
          <ul className="recommendations-list">
            {topic.recommendedActivities.map((activity, index) => (
              <li key={index} className="recommendation-item">
                <div className="recommendation-icon">📋</div>
                <span>{activity}</span>
              </li>
            ))}
          </ul>
          
          <button className="create-activity-button">
            Create Custom Activity
          </button>
        </div>
      </div>
    </div>
  );
}

export default TopicProgressPage; 