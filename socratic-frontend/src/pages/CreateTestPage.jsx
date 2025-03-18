import React, { useState } from 'react';
import TeacherQuestionForm from '../components/TeacherQuestionForm';
import { Link } from 'react-router-dom';
import '../styles/CreateTestPage.css';

function CreateTestPage() {
  const [questions, setQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState({
    publicQuestion: '',
    hiddenValuesRaw: '',
    hiddenValues: {},
    answer: '',
    formula: '',
    teacherInstructions: '',
    hintLevel: 'easy',
    subject: '',
    topic: '',
    image: null
  });
  const [testCode, setTestCode] = useState('');
  const [testName, setTestName] = useState('');
  const [testSubmitted, setTestSubmitted] = useState(false);

  // helper for generating a random test code if teacher leaves it blank
  const generateTestCode = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
  };

  // Add image upload handler
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setNewQuestion(prev => ({
        ...prev,
        image: file
      }));
    }
  };

  // Modify addQuestion to handle image upload
  const addQuestion = async (e) => {
    e.preventDefault();
    
    let imageUrl = null;
    if (newQuestion.image) {
      const formData = new FormData();
      formData.append('image', newQuestion.image);
      
      try {
        const response = await fetch('http://localhost:8000/upload-image', {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          const data = await response.json();
          imageUrl = data.image_url;
        }
      } catch (error) {
        console.error('Error uploading image:', error);
      }
    }

    // Format question according to the expected structure
    const formattedQuestion = {
      public_question: newQuestion.publicQuestion,
      hidden_values: newQuestion.hiddenValues,
      answer: newQuestion.answer,
      formula: newQuestion.formula || '',
      teacher_instructions: newQuestion.teacherInstructions || '',
      hint_level: newQuestion.hintLevel || 'easy',
      subject: newQuestion.subject || '',
      topic: newQuestion.topic || '',
      image_url: imageUrl
    };

    setQuestions(prev => [...prev, formattedQuestion]);
    // Reset form for next question
    setNewQuestion({
      publicQuestion: '',
      hiddenValuesRaw: '',
      hiddenValues: {},
      answer: '',
      formula: '',
      teacherInstructions: '',
      hintLevel: 'easy',
      subject: '',
      topic: '',
      image: null
    });
  };

  // Send the test data to the backend endpoint
  const createTest = async () => {
    const finalTestCode = testCode.trim() !== '' ? testCode : generateTestCode();
    const testData = {
      code: finalTestCode,
      name: testName,
      questions: questions,
    };

    try {
      const response = await fetch('http://localhost:8000/tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testData),
      });

      if (response.ok) {
        alert(`Test created successfully! Test code: ${finalTestCode}`);
        setTestSubmitted(true);
      } else {
        const errorData = await response.json();
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
            onImageUpload={handleImageUpload}
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