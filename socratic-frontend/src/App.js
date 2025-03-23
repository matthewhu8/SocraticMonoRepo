//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import PhysicsProblemPage from './pages/PhysicProblemPage';
import TeacherDashboardPage from './pages/TeacherDashboardPage';
import CreateTestPage from './pages/CreateTestPage';
import CreatePracticeExamPage from './pages/CreatePracticeExamPage';
import StudentDashboardPage from './pages/StudentDashboardPage';
import AssessmentPage from './pages/AssessmentPage';
import TestPage from './pages/TestPage';
import TopicProgressPage from './pages/TopicProgressPage';

// Empty placeholder component for Learning Modules
const LearningModulesPlaceholder = () => (
  <div style={{ 
    padding: '2rem', 
    textAlign: 'center', 
    maxWidth: '800px', 
    margin: '0 auto',
    marginTop: '2rem'
  }}>
    <h1>Learning Modules</h1>
    <p>This feature is coming soon.</p>
    <button 
      onClick={() => window.history.back()} 
      style={{ 
        padding: '0.5rem 1rem', 
        marginTop: '1rem',
        background: '#3498db',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    >
      Back to Dashboard
    </button>
  </div>
);

// Placeholder component for Create Learning Module
const CreateLearningModulePlaceholder = () => (
  <div style={{ 
    padding: '2rem', 
    textAlign: 'center', 
    maxWidth: '800px', 
    margin: '0 auto',
    marginTop: '2rem'
  }}>
    <h1>Create Learning Module</h1>
    <p>This feature is coming soon. We're working on building tools to help you create interactive learning experiences for your students.</p>
    <button 
      onClick={() => window.history.back()} 
      style={{ 
        padding: '0.5rem 1rem', 
        marginTop: '1rem',
        background: '#3498db',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    >
      Back to Dashboard
    </button>
  </div>
);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/problem" element={<PhysicsProblemPage />} />
        <Route path="/student" element={<StudentDashboardPage />} />
        <Route path="/teachers" element={<TeacherDashboardPage />} />
        <Route path="/teachers/create-test" element={<CreateTestPage />} />
        <Route path="/teachers/create-practice-exam" element={<CreatePracticeExamPage />} />
        <Route path="/teachers/create-learning-module" element={<CreateLearningModulePlaceholder />} />
        <Route path="/teachers/topic/:topicId" element={<TopicProgressPage />} />
        
        {/* Student section routes */}
        <Route path="/student/learning-modules" element={<LearningModulesPlaceholder />} />
        <Route path="/student/practice" element={<PhysicsProblemPage />} />
        <Route path="/student/assessment" element={<AssessmentPage />} />
        <Route path="/student/assessment/test/:testCode" element={<TestPage />} />
        <Route path="/student/assessment/review/:assessmentId" element={<PhysicsProblemPage />} />
      </Routes>
    </Router>
  );
}

export default App;