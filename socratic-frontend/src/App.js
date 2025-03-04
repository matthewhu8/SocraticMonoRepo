//// filepath: /Users/matthewhu/Code/SocraticMonoRepo/socratic-frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import PhysicsProblemPage from './pages/PhysicProblemPage';
import TeacherDashboardPage from './pages/TeacherDashboardPage';
import CreateTestPage from './pages/CreateTestPage';
import StudentDashboardPage from './pages/StudentDashboardPage';
import AssessmentPage from './pages/AssessmentPage';
import TestPage from './pages/TestPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/problem" element={<PhysicsProblemPage />} />
        <Route path="/student" element={<StudentDashboardPage />} />
        <Route path="/teachers" element={<TeacherDashboardPage />} />
        <Route path="/teachers/create-test" element={<CreateTestPage />} />
        
        {/* Student section routes */}
        <Route path="/student/learning-modules" element={<PhysicsProblemPage />} />
        <Route path="/student/practice" element={<PhysicsProblemPage />} />
        <Route path="/student/assessment" element={<AssessmentPage />} />
        <Route path="/student/assessment/test/:testCode" element={<TestPage />} />
        <Route path="/student/assessment/review/:assessmentId" element={<PhysicsProblemPage />} />
      </Routes>
    </Router>
  );
}

export default App;