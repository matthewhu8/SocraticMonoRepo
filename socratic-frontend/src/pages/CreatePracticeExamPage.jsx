import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/CreateTestPage.css';

function CreatePracticeExamPage() {
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
  const [editingIndex, setEditingIndex] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [hiddenValuesRaw, setHiddenValuesRaw] = useState('');

  // helper for generating a random test code if teacher leaves it blank
  const generateTestCode = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
  };

  // Parse hidden values input into an object when it changes
  const handleHiddenValuesChange = (e) => {
    const valuesString = e.target.value;
    setHiddenValuesRaw(valuesString);
    
    // Try to parse it into an object format for storage
    try {
      // Split by commas, then by equals sign
      const valuesObj = {};
      valuesString.split(',').forEach(pair => {
        const [key, value] = pair.trim().split('=');
        if (key && value) {
          // Try to convert to number if possible
          const numValue = parseFloat(value);
          valuesObj[key.trim()] = isNaN(numValue) ? value.trim() : numValue;
        }
      });
      setNewQuestion({ 
        ...newQuestion, 
        hiddenValues: valuesObj 
      });
    } catch (error) {
      console.error("Error parsing hidden values:", error);
    }
  };

  const addQuestion = (e) => {
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

    if (isEditing && editingIndex !== null) {
      // Update existing question
      const updatedQuestions = [...questions];
      updatedQuestions[editingIndex] = formattedQuestion;
      setQuestions(updatedQuestions);
      setIsEditing(false);
      setEditingIndex(null);
    } else {
      // Add new question
      setQuestions(prev => [...prev, formattedQuestion]);
    }

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
    setHiddenValuesRaw('');
  };

  const editQuestion = (index) => {
    const questionToEdit = questions[index];
    
    // Convert the question format back to the form format
    setNewQuestion({
      publicQuestion: questionToEdit.public_question,
      hiddenValues: questionToEdit.hidden_values,
      answer: questionToEdit.answer,
      formula: questionToEdit.formula,
      teacherInstructions: questionToEdit.teacher_instructions,
      hintLevel: questionToEdit.hint_level,
      subject: questionToEdit.subject,
      topic: questionToEdit.topic
    });
    
    // Set raw hidden values for display
    setHiddenValuesRaw(
      Object.entries(questionToEdit.hidden_values)
        .map(([key, value]) => `${key}=${value}`)
        .join(', ')
    );
    
    setEditingIndex(index);
    setIsEditing(true);
    
    // Scroll to the form
    document.querySelector('.question-form-section').scrollIntoView({ behavior: 'smooth' });
  };

  const deleteQuestion = (index) => {
    if (window.confirm('Are you sure you want to delete this question?')) {
      const updatedQuestions = [...questions];
      updatedQuestions.splice(index, 1);
      setQuestions(updatedQuestions);
      
      // If we were editing this question, reset the form
      if (isEditing && editingIndex === index) {
        setIsEditing(false);
        setEditingIndex(null);
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
        setHiddenValuesRaw('');
      }
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setEditingIndex(null);
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
    setHiddenValuesRaw('');
  };

  // Send the practice exam data to the backend endpoint
  const createPracticeExam = async () => {
    if (questions.length === 0) {
      alert("Please add at least one question to the practice exam.");
      return;
    }

    if (!testName.trim()) {
      alert("Please enter a practice exam name.");
      return;
    }

    const examData = {
      name: testName,
      code: testCode || generateTestCode(),
      isPracticeExam: true,
      questions: questions
    };

    try {
      const response = await fetch('http://localhost:8000/tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(examData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        console.error('Failed to create practice exam:', response.status, errorData);
        alert(`Failed to create practice exam: ${response.statusText}`);
        return;
      }

      console.log('Practice exam created successfully');
      setTestSubmitted(true);
      setQuestions([]);
      setTestName('');
      setTestCode('');
      setNewQuestion({
        publicQuestion: '',
        hiddenValues: {},
        answer: '',
        formula: '',
        teacherInstructions: '',
        hintLevel: 'basic',
        subject: '',
        topic: ''
      });
    } catch (error) {
      console.error('Error:', error);
      alert(`Error creating practice exam: ${error.message}`);
    }
  };

  return (
    <div className="create-test-container">
      <div className="create-test-header">
        <h1>Create Practice Exam</h1>
        <p>Build an interactive practice exam with AI-powered feedback for your students</p>
      </div>
      
      <div className="content-panel">
        <div className="test-code-section">
          <h3>Practice Exam Information</h3>
          <div className="input-group">
            <label>
              Practice Exam Name:
              <input
                type="text"
                value={testName}
                onChange={(e) => setTestName(e.target.value)}
                placeholder="Enter practice exam name"
                required
              />
            </label>
          </div>
          <div className="input-group">
            <label>
              Access Code (optional, leave blank to auto-generate):
              <input
                type="text"
                value={testCode}
                onChange={(e) => setTestCode(e.target.value)}
                placeholder="Enter custom access code"
              />
            </label>
          </div>
        </div>
        
        <div className="question-form-section">
          <h3 className={isEditing ? 'editing-title' : ''}>{isEditing ? 'Edit Question' : 'Add a New Question'}</h3>
          <form onSubmit={addQuestion} className="question-form">
            <div className="form-group">
              <label>
                Public Question (required):<br />
                <textarea
                  value={newQuestion.publicQuestion || ''}
                  onChange={(e) => setNewQuestion({ ...newQuestion, publicQuestion: e.target.value })}
                  required
                  className="form-textarea"
                  placeholder="What is the sum of x and y?"
                />
              </label>
            </div>
            
            <div className="form-group">
              <label>
                Hidden Values (required):<br />
                <input
                  type="text"
                  value={hiddenValuesRaw}
                  onChange={handleHiddenValuesChange}
                  required
                  className="form-input"
                  placeholder="e.g. x=3, y=10"
                />
              </label>
              <small className="form-tip">Format: var1=value1, var2=value2</small>
            </div>
            
            <div className="form-group">
              <label>
                Answer (required):<br />
                <input
                  type="text"
                  value={newQuestion.answer || ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Try to convert to number if possible
                    const numValue = parseFloat(value);
                    setNewQuestion({ ...newQuestion, answer: isNaN(numValue) ? value : numValue });
                  }}
                  required
                  className="form-input"
                  placeholder="e.g. 13"
                />
              </label>
            </div>
            
            <div className="form-group">
              <label>
                Formula (optional):<br />
                <input
                  type="text"
                  value={newQuestion.formula || ''}
                  onChange={(e) => setNewQuestion({ ...newQuestion, formula: e.target.value })}
                  className="form-input"
                  placeholder="e.g. sum = x + y"
                />
              </label>
            </div>
            
            <div className="form-group">
              <label>
                Teacher Instructions (optional):<br />
                <textarea
                  value={newQuestion.teacherInstructions || ''}
                  onChange={(e) => setNewQuestion({ ...newQuestion, teacherInstructions: e.target.value })}
                  className="form-textarea"
                  placeholder="Guide students to discover both variables before solving..."
                />
              </label>
            </div>
            
            <div className="form-row">
              <div className="form-group form-group-half">
                <label>
                  Hint Level:
                  <select
                    value={newQuestion.hintLevel || 'easy'}
                    onChange={(e) => setNewQuestion({ ...newQuestion, hintLevel: e.target.value })}
                    className="form-select"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </label>
              </div>
              
              <div className="form-group form-group-half">
                <label>
                  Subject:
                  <input
                    type="text"
                    value={newQuestion.subject || ''}
                    onChange={(e) => setNewQuestion({ ...newQuestion, subject: e.target.value })}
                    className="form-input"
                    placeholder="e.g. mathematics"
                  />
                </label>
              </div>
            </div>
            
            <div className="form-group">
              <label>
                Topic:
                <input
                  type="text"
                  value={newQuestion.topic || ''}
                  onChange={(e) => setNewQuestion({ ...newQuestion, topic: e.target.value })}
                  className="form-input"
                  placeholder="e.g. basic_arithmetic"
                />
              </label>
            </div>
            
            <button type="submit" className={`add-question-btn ${isEditing ? 'editing' : ''}`}>
              {isEditing ? 'Update Question' : 'Add Question'}
            </button>
          </form>
          {isEditing && (
            <button className="cancel-edit-button" onClick={cancelEdit}>
              Cancel Edit
            </button>
          )}
        </div>
        
        <div className="questions-list-section">
          <h3>Questions Added ({questions.length})</h3>
          {questions.length === 0 ? (
            <div className="empty-state">
              <p>No questions added yet.</p>
              <p className="hint">Use the form above to add questions to your practice exam.</p>
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
                    <p><strong>Hint Level:</strong> {q.hint_level}</p>
                    <p><strong>Subject:</strong> {q.subject || 'Not specified'}</p>
                    <p><strong>Topic:</strong> {q.topic || 'Not specified'}</p>
                    {q.teacher_instructions && <p><strong>Instructions:</strong> {q.teacher_instructions}</p>}
                  </div>
                  <div className="question-actions">
                    <button 
                      className="edit-question-button" 
                      onClick={() => editQuestion(index)}
                      aria-label="Edit question"
                    >
                      ✏️
                    </button>
                    <button 
                      className="delete-question-button" 
                      onClick={() => deleteQuestion(index)}
                      aria-label="Delete question"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="actions-section">
          {questions.length > 0 && (
            <button className="create-button" onClick={createPracticeExam}>
              Create Practice Exam
            </button>
          )}
          {testSubmitted && (
            <p className="success-message">Practice exam has been submitted successfully!</p>
          )}
          <Link to="/teachers" className="back-link">Back to Teacher Dashboard</Link>
        </div>
      </div>
    </div>
  );
}

export default CreatePracticeExamPage; 