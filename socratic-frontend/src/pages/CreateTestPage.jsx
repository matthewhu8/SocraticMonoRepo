import React, { useState } from 'react';
import TeacherQuestionForm from '../components/TeacherQuestionForm';
import { Link } from 'react-router-dom';
import '../styles/CreateTestPage.css';

function CreateTestPage() {
  const [questions, setQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState({
    publicQuestion: '',
    hiddenValues: {},
    answer: '',
    formula: '',
    teacherInstructions: '',
    hintLevel: 'easy',
    subject: '',
    topic: ''
  });
  const [testCode, setTestCode] = useState('');
  const [testName, setTestName] = useState('');
  const [testSubmitted, setTestSubmitted] = useState(false);

  // helper for generating a random test code if teacher leaves it blank
  const generateTestCode = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
  };

  const addQuestion = async (e) => {
    e.preventDefault();
    
    // Format question according to the expected structure
    const formattedQuestion = {
      public_question: newQuestion.publicQuestion,
      hidden_values: newQuestion.hiddenValues,
      answer: String(newQuestion.answer),
      formula: newQuestion.formula || '',
      teacher_instructions: newQuestion.teacherInstructions || '',
      hint_level: newQuestion.hintLevel || 'easy',
      subject: newQuestion.subject || '',
      topic: newQuestion.topic || ''
    };

    setQuestions(prev => [...prev, formattedQuestion]);
    // Reset form for next question
    setNewQuestion({
      publicQuestion: '',
      hiddenValues: {},
      answer: '',
      formula: '',
      teacherInstructions: '',
      hintLevel: 'easy',
      subject: '',
      topic: ''
    });
  };

  // Send the test data to the backend endpoint
  const createTest = async () => {
    const finalTestCode = testCode.trim() !== '' ? testCode : generateTestCode();
    
    // Create properly structured test data object
    const testData = {
      name: testName,
      code: finalTestCode,
      questions: questions
    };

    // Add console log to inspect the data being sent
    console.log("Sending test data to backend:", {
      testData: testData,
      jsonString: JSON.stringify(testData, null, 2)
    });

    try {
      const response = await fetch('http://localhost:8000/tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData)
      });

      // Log response status
      console.log("Response status:", response.status);
      
      if (response.ok) {
        alert(`Test created successfully! Test code: ${finalTestCode}`);
        setTestSubmitted(true);
      } else {
        const errorData = await response.json();
        console.log("Error response:", errorData);
        alert(`Failed to create test: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error("Error creating test:", error);
      alert("An error occurred while creating the test.");
    }
  };

  return (
    <div className="create-test-container">
      <div className="create-test-header">
        <h1>Create Test</h1>
        <p>Add questions and generate a test code for your students</p>
      </div>
      
      <div className="content-panel">
        <div className="test-code-section">
          <h3>Test Information</h3>
          <div className="input-group">
            <label>
              Test Name:
              <input
                type="text"
                value={testName}
                onChange={(e) => setTestName(e.target.value)}
                placeholder="Enter test name"
                required
              />
            </label>
          </div>
          <div className="input-group">
            <label>
              Test Code (optional, leave blank to auto-generate):
              <input
                type="text"
                value={testCode}
                onChange={(e) => setTestCode(e.target.value)}
                placeholder="Enter custom test code"
              />
            </label>
          </div>
        </div>
        
        <div className="question-form-section">
          <h3>Add a New Question</h3>
          <TeacherQuestionForm
            newQuestion={newQuestion}
            setNewQuestion={setNewQuestion}
            onSubmit={addQuestion}
          />
        </div>
        
        <div className="questions-list-section">
          <h3>Questions Added ({questions.length})</h3>
          {questions.length === 0 ? (
            <div className="empty-state">
              <p>No questions added yet.</p>
              <p className="hint">Use the form above to add questions to your test.</p>
            </div>
          ) : (
            <div className="questions-grid">
              {questions.map((q, index) => (
                <div key={index} className="question-card">
                  <div className="question-number">{index + 1}</div>
                  <div className="question-details">
                    <p><strong>Question:</strong> {q.public_question}</p>
                    <p><strong>Hidden Values:</strong> {Object.entries(q.hidden_values)
                      .map(([key, value]) => `${key}=${value}`)
                      .join(', ')}
                    </p>
                    <p><strong>Answer:</strong> {q.answer}</p>
                    {q.formula && <p><strong>Formula:</strong> {q.formula}</p>}
                    <p><strong>Subject:</strong> {q.subject || 'Not specified'}</p>
                    <p><strong>Topic:</strong> {q.topic || 'Not specified'}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="actions-section">
          {questions.length > 0 && (
            <button className="create-button" onClick={createTest}>
              Create Test
            </button>
          )}
          {testSubmitted && (
            <p className="success-message">Test has been submitted successfully!</p>
          )}
          <Link to="/teachers" className="back-link">Back to Teacher Dashboard</Link>
        </div>
      </div>
    </div>
  );
}

export default CreateTestPage;