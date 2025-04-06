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
import StudentAuthPage from './pages/StudentAuthPage';
import TeacherAuthPage from './pages/TeacherAuthPage';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

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
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/problem" element={<PhysicsProblemPage />} />
          
          {/* Authentication routes */}
          <Route path="/student/auth" element={<StudentAuthPage />} />
          <Route path="/teachers/auth" element={<TeacherAuthPage />} />
          
          {/* Dashboard routes - these will be accessed after authentication */}
          <Route 
            path="/student/dashboard" 
            element={
              <ProtectedRoute requiredRole="student">
                <StudentDashboardPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teachers/dashboard" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <TeacherDashboardPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Keep existing routes as fallbacks */}
          <Route path="/student" element={<StudentAuthPage />} />
          <Route path="/teachers" element={<TeacherAuthPage />} />
          
          {/* Protected Teacher routes */}
          <Route 
            path="/teachers/create-test" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <CreateTestPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teachers/create-practice-exam" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <CreatePracticeExamPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teachers/create-learning-module" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <CreateLearningModulePlaceholder />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/teachers/topic/:topicId" 
            element={
              <ProtectedRoute requiredRole="teacher">
                <TopicProgressPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Protected Student routes */}
          <Route 
            path="/student/learning-modules" 
            element={
              <ProtectedRoute requiredRole="student">
                <LearningModulesPlaceholder />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/practice" 
            element={
              <ProtectedRoute requiredRole="student">
                <PhysicsProblemPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/assessment" 
            element={
              <ProtectedRoute requiredRole="student">
                <AssessmentPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/assessment/test/:testCode" 
            element={
              <ProtectedRoute requiredRole="student">
                <TestPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/student/assessment/review/:assessmentId" 
            element={
              <ProtectedRoute requiredRole="student">
                <PhysicsProblemPage />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;