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
      'business-organization': {
        id: 'business-organization',
        name: 'Business Organization',
        description: 'Understanding organizational objectives, stakeholders, and organizational structures',
        status: 'Needs Review',
        overallProgress: 65,
        studentProgress: [
          { id: 1, name: "Sarah Johnson", mastery: 55, image: "https://i.pravatar.cc/150?img=1", strengths: "Stakeholder analysis", weaknesses: "Organizational structures" },
          { id: 2, name: "Michael Chen", mastery: 48, image: "https://i.pravatar.cc/150?img=2", strengths: "Understanding concepts", weaknesses: "Case study application" },
          { id: 3, name: "Emma Davis", mastery: 92, image: "https://i.pravatar.cc/150?img=3", strengths: "All organization topics", weaknesses: "None significant" },
          { id: 4, name: "James Wilson", mastery: 38, image: "https://i.pravatar.cc/150?img=4", strengths: "Basic concepts", weaknesses: "Organizational objectives" },
          { id: 5, name: "Sofia Rodriguez", mastery: 78, image: "https://i.pravatar.cc/150?img=5", strengths: "Ethics, CSR", weaknesses: "Org. structures" },
          { id: 6, name: "Aiden Patel", mastery: 60, image: "https://i.pravatar.cc/150?img=6", strengths: "Cultural differences", weaknesses: "Stakeholder analysis" },
          { id: 7, name: "Isabella Kim", mastery: 95, image: "https://i.pravatar.cc/150?img=7", strengths: "All topics", weaknesses: "None" },
          { id: 8, name: "Lucas Thompson", mastery: 42, image: "https://i.pravatar.cc/150?img=8", strengths: "Basic principles", weaknesses: "Complex organizations" },
          { id: 9, name: "Olivia Martinez", mastery: 72, image: "https://i.pravatar.cc/150?img=9", strengths: "Understanding concepts", weaknesses: "Application" },
          { id: 10, name: "Ethan Nguyen", mastery: 58, image: "https://i.pravatar.cc/150?img=10", strengths: "Org. structure types", weaknesses: "Stakeholder concerns" },
          { id: 11, name: "Ava Williams", mastery: 82, image: "https://i.pravatar.cc/150?img=11", strengths: "Most organization topics", weaknesses: "Complex case studies" },
          { id: 12, name: "Noah Garcia", mastery: 65, image: "https://i.pravatar.cc/150?img=12", strengths: "Basic structures", weaknesses: "Evaluating structures" }
        ],
        recommendedActivities: [
          "Organizational Structure Analysis: Compare and contrast different business structures",
          "Stakeholder Mapping: Identify key stakeholders and their influence",
          "Interactive Case Studies: Apply organizational concepts to real businesses",
          "Corporate Social Responsibility: Evaluate CSR initiatives and their impact"
        ]
      },
      'human-resources': {
        id: 'human-resources',
        name: 'Human Resource Management',
        description: 'Functions and methods of human resource management in organizations',
        status: 'Strong Performance',
        overallProgress: 90,
        studentProgress: [
          { id: 1, name: "Sarah Johnson", mastery: 88, image: "https://i.pravatar.cc/150?img=1", strengths: "Recruitment", weaknesses: "Training methods" },
          { id: 2, name: "Michael Chen", mastery: 95, image: "https://i.pravatar.cc/150?img=2", strengths: "All HR concepts", weaknesses: "None" },
          { id: 3, name: "Emma Davis", mastery: 97, image: "https://i.pravatar.cc/150?img=3", strengths: "All HR concepts", weaknesses: "None" },
          { id: 4, name: "James Wilson", mastery: 78, image: "https://i.pravatar.cc/150?img=4", strengths: "Basic HR functions", weaknesses: "Strategic HRM" },
          { id: 5, name: "Sofia Rodriguez", mastery: 92, image: "https://i.pravatar.cc/150?img=5", strengths: "Performance management", weaknesses: "None significant" },
          { id: 6, name: "Aiden Patel", mastery: 89, image: "https://i.pravatar.cc/150?img=6", strengths: "Most HR concepts", weaknesses: "Industrial relations" },
          { id: 7, name: "Isabella Kim", mastery: 98, image: "https://i.pravatar.cc/150?img=7", strengths: "All HR concepts", weaknesses: "None" },
          { id: 8, name: "Lucas Thompson", mastery: 83, image: "https://i.pravatar.cc/150?img=8", strengths: "Recruitment, selection", weaknesses: "Compensation" },
          { id: 9, name: "Olivia Martinez", mastery: 94, image: "https://i.pravatar.cc/150?img=9", strengths: "All HR concepts", weaknesses: "None significant" },
          { id: 10, name: "Ethan Nguyen", mastery: 87, image: "https://i.pravatar.cc/150?img=10", strengths: "Training methods", weaknesses: "Strategic aspects" },
          { id: 11, name: "Ava Williams", mastery: 91, image: "https://i.pravatar.cc/150?img=11", strengths: "Most HR concepts", weaknesses: "None significant" },
          { id: 12, name: "Noah Garcia", mastery: 88, image: "https://i.pravatar.cc/150?img=12", strengths: "Selection processes", weaknesses: "Legal frameworks" }
        ],
        recommendedActivities: [
          "Advanced HRM: Develop strategic human resource plans",
          "Enrichment: Training and development program design",
          "Challenge Problems: Complex compensation package analysis",
          "Independent Study: Exploration of cultural dimensions in global HRM"
        ]
      },
      'marketing': {
        id: 'marketing',
        name: 'Marketing',
        description: 'Marketing objectives, planning, and the 4Ps (product, price, promotion, place)',
        status: 'Needs Attention',
        overallProgress: 62,
        studentProgress: [
          { id: 1, name: "Sarah Johnson", mastery: 68, image: "https://i.pravatar.cc/150?img=1", strengths: "Product strategies", weaknesses: "Pricing strategies" },
          { id: 2, name: "Michael Chen", mastery: 55, image: "https://i.pravatar.cc/150?img=2", strengths: "Promotion", weaknesses: "Market research" },
          { id: 3, name: "Emma Davis", mastery: 85, image: "https://i.pravatar.cc/150?img=3", strengths: "Most marketing areas", weaknesses: "E-marketing" },
          { id: 4, name: "James Wilson", mastery: 42, image: "https://i.pravatar.cc/150?img=4", strengths: "Basic concepts", weaknesses: "Marketing mix application" },
          { id: 5, name: "Sofia Rodriguez", mastery: 72, image: "https://i.pravatar.cc/150?img=5", strengths: "Market segmentation", weaknesses: "Pricing strategies" },
          { id: 6, name: "Aiden Patel", mastery: 58, image: "https://i.pravatar.cc/150?img=6", strengths: "Product life cycle", weaknesses: "Marketing planning" },
          { id: 7, name: "Isabella Kim", mastery: 90, image: "https://i.pravatar.cc/150?img=7", strengths: "All marketing concepts", weaknesses: "None significant" },
          { id: 8, name: "Lucas Thompson", mastery: 48, image: "https://i.pravatar.cc/150?img=8", strengths: "Promotion strategies", weaknesses: "Market research" },
          { id: 9, name: "Olivia Martinez", mastery: 65, image: "https://i.pravatar.cc/150?img=9", strengths: "Understanding 4Ps", weaknesses: "Extended marketing mix" },
          { id: 10, name: "Ethan Nguyen", mastery: 52, image: "https://i.pravatar.cc/150?img=10", strengths: "Place (distribution)", weaknesses: "Digital marketing" },
          { id: 11, name: "Ava Williams", mastery: 78, image: "https://i.pravatar.cc/150?img=11", strengths: "Most marketing areas", weaknesses: "International marketing" },
          { id: 12, name: "Noah Garcia", mastery: 60, image: "https://i.pravatar.cc/150?img=12", strengths: "Understanding concepts", weaknesses: "Applying the marketing mix" }
        ],
        recommendedActivities: [
          "Marketing Mix Framework: Practice applying the 4Ps to different business scenarios",
          "Market Research Techniques: Methods and analysis practice",
          "Guided Practice: Step-by-step breakdowns of successful marketing campaigns",
          "Real-world Applications: Create marketing plans for real businesses"
        ]
      }
    };

    // If no specific identifier or not found, return the first topic
    if (!identifier || !topics[identifier.toLowerCase()]) {
      return topics['business-organization'];
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