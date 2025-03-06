import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import ProblemDisplay from '../components/ProblemDisplay';
import ChatBox from '../components/ChatBox';
import '../styles/TestPage.css';

function TestPage() {
  const { testCode } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [testData, setTestData] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [messages, setMessages] = useState([]);
  const [answers, setAnswers] = useState({});
  const [testCompleted, setTestCompleted] = useState(false);

  // Fetch test data when component mounts
  useEffect(() => {
    const fetchTest = async () => {
      try {
        console.log(`Attempting to fetch test with code: ${testCode}`);
        setLoading(true);
        const response = await fetch(`http://127.0.0.1:8000/tests/${testCode}`);
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Test not found. Please check the test code and try again.');
          }
          throw new Error(`Error fetching test: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Test data received:', JSON.stringify(data, null, 2));
        console.log('Number of questions:', data.questions ? data.questions.length : 0);
        
        if (data.questions && data.questions.length > 0) {
          console.log('First question sample:', data.questions[0]);
        } else {
          console.warn('No questions found in the test data');
        }
        
        setTestData(data);
        const initialMessages = {};
        if (data.questions) {
          data.questions.forEach((_, index) => {
            initialMessages[index] = [];
          });
        }
        setMessages(initialMessages);
      } catch (error) {
        console.error('Error fetching test:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTest();
  }, [testCode]);

  // Get current question data
  const getCurrentQuestion = () => {
    if (!testData || !testData.questions || testData.questions.length === 0) {
      return null;
    }
    
    const question = testData.questions[currentQuestionIndex];
    console.log("Current question data:", question);
    
    // Ensure consistent field access regardless of naming convention
    return {
      // Original fields
      ...question,
      
      // Normalized fields (ensure both naming conventions work)
      publicQuestion: question.publicQuestion || question.public_question,
      public_question: question.public_question || question.publicQuestion,
      hiddenValues: question.hiddenValues || question.hidden_values,
      hidden_values: question.hidden_values || question.hiddenValues,
      imageUrl: question.imageUrl || question.image_url
    };
  };

  const currentQuestion = getCurrentQuestion();
  
  const handleSendMessage = async (text) => {
    const questionId = currentQuestionIndex;
    
    console.log("Sending message for question:", questionId);
    console.log("Message text:", text);
    
    // Add user message
    const userMessage = { sender: 'User', text };
    setMessages(prev => ({
      ...prev,
      [questionId]: [...(prev[questionId] || []), userMessage]
    }));
  
    try {
      // Use a default problem_id (e.g., 1) since we're now using test_code and question_index
      const problemId = 1;
      
      console.log("Sending chat request with:", {
        problem_id: problemId,
        query: text,
        test_code: testCode,
        question_index: currentQuestionIndex
      });
      
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_id: problemId,
          query: text,
          test_code: testCode, // Include the test code
          question_index: currentQuestionIndex, // Include the current question index
        }),
      });
      
      if (!response.ok) {
        console.error("Chat response error:", response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Chat response received:", data);
      
      const aiMessage = { sender: 'AI', text: data.response };
      
      setMessages(prev => ({
        ...prev,
        [questionId]: [...(prev[questionId] || []), aiMessage]
      }));
      
      // Check if the message looks like an answer attempt
      const numberMatch = text.match(/\b\d+(\.\d+)?\b/);
      if (numberMatch) {
        const answerValue = numberMatch[0];
        console.log(`Detected potential answer: ${answerValue}`);
        setAnswers(prev => ({
          ...prev,
          [questionId]: answerValue
        }));
      }
    } catch (error) {
      console.error('Error fetching AI response:', error);
      const errorMessage = { sender: 'System', text: 'Error: Unable to get response from AI.' };
      setMessages(prev => ({
        ...prev,
        [questionId]: [...(prev[questionId] || []), errorMessage]
      }));
    }
  };

  const navigateToNextQuestion = () => {
    if (currentQuestionIndex < testData.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      // If this is the last question, mark the test as completed
      setTestCompleted(true);
    }
  };

  const navigateToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const submitTest = () => {
    // In a real implementation, you would send the answers to the server here
    alert('Test submitted successfully!');
    navigate('/student/assessment');
  };

  // Debug panel component
  const DebugPanel = () => {
    const [showDebug, setShowDebug] = useState(false);
    
    return (
      <div className="debug-panel">
        <button 
          onClick={() => setShowDebug(!showDebug)} 
          className="debug-toggle"
        >
          {showDebug ? "Hide Debug Info" : "Show Debug Info"}
        </button>
        
        {showDebug && (
          <div className="debug-content">
            <h3>Debug Information</h3>
            <div className="debug-section">
              <h4>Test Data:</h4>
              <pre>{JSON.stringify(testData, null, 2)}</pre>
            </div>
            <div className="debug-section">
              <h4>Current Question:</h4>
              <pre>{JSON.stringify(currentQuestion, null, 2)}</pre>
            </div>
            <div className="debug-section">
              <h4>Messages for Current Question:</h4>
              <pre>{JSON.stringify(messages[currentQuestionIndex] || [], null, 2)}</pre>
            </div>
            <div className="debug-section">
              <h4>Answers:</h4>
              <pre>{JSON.stringify(answers, null, 2)}</pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="test-page-container">
        <div className="sticky-nav">
          <div className="nav-container">
            <Link to="/" className="nav-item">
              <span className="nav-label">Socratic</span>
            </Link>
            <Link to="/student" className="nav-item">
              <span className="nav-label">Student Dashboard</span>
            </Link>
          </div>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading test...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="test-page-container">
        <div className="sticky-nav">
          <div className="nav-container">
            <Link to="/" className="nav-item">
              <span className="nav-label">Socratic</span>
            </Link>
            <Link to="/student" className="nav-item">
              <span className="nav-label">Student Dashboard</span>
            </Link>
          </div>
        </div>
        <div className="error-container">
          <h2>Error Loading Test</h2>
          <p>{error}</p>
          <button 
            className="back-button"
            onClick={() => navigate('/student/assessment')}
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  if (testCompleted) {
    return (
      <div className="test-page-container">
        <div className="sticky-nav">
          <div className="nav-container">
            <Link to="/" className="nav-item">
              <span className="nav-label">Socratic</span>
            </Link>
            <Link to="/student" className="nav-item">
              <span className="nav-label">Student Dashboard</span>
            </Link>
          </div>
        </div>
        <div className="test-complete-container">
          <h2>Test Complete!</h2>
          <div className="test-summary">
            <h3>Your Answers:</h3>
            <ul>
              {testData.questions.map((question, index) => (
                <li key={index}>
                  <p>
                    <strong>Question {index + 1}:</strong> {
                      question.public_question || 
                      question.publicQuestion || 
                      "No question text"
                    }
                  </p>
                  <p><strong>Your answer:</strong> {answers[index] || "Not answered"}</p>
                </li>
              ))}
            </ul>
          </div>
          <button 
            className="submit-button"
            onClick={submitTest}
          >
            Submit Test
          </button>
          <button 
            className="review-button"
            onClick={() => setTestCompleted(false)}
          >
            Review Answers
          </button>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="test-page-container">
        <div className="sticky-nav">
          <div className="nav-container">
            <Link to="/" className="nav-item">
              <span className="nav-label">Socratic</span>
            </Link>
            <Link to="/student" className="nav-item">
              <span className="nav-label">Student Dashboard</span>
            </Link>
          </div>
        </div>
        <div className="error-container">
          <h2>No Questions Found</h2>
          <p>This test does not contain any questions.</p>
          <button 
            className="back-button"
            onClick={() => navigate('/student/assessment')}
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="test-page-container">
      <div className="sticky-nav">
        <div className="nav-container">
          <Link to="/" className="nav-item">
            <span className="nav-label">Socratic</span>
          </Link>
          <Link to="/student" className="nav-item">
            <span className="nav-label">Student Dashboard</span>
          </Link>
        </div>
      </div>
      <div className="test-header">
        <h1>{testData.name}</h1>
        <div className="question-progress">
          Question {currentQuestionIndex + 1} of {testData.questions.length}
        </div>
      </div>
      
      <div className="test-content">
        <ProblemDisplay 
          problem={{
            title: `Question ${currentQuestionIndex + 1}`,
            description: currentQuestion.public_question || currentQuestion.publicQuestion || "No question text",
            imageUrl: currentQuestion.imageUrl || currentQuestion.image_url || ""
          }} 
        />
        
        <div className="chat-container">
          <ChatBox 
            onSendMessage={handleSendMessage} 
            messages={messages[currentQuestionIndex] || []} 
          />
        </div>
        
        <div className="answer-status">
          {answers[currentQuestionIndex] ? (
            <div className="answer-provided">
              Your answer: {answers[currentQuestionIndex]}
            </div>
          ) : (
            <div className="no-answer">
              No answer provided yet
            </div>
          )}
        </div>
        
        <div className="navigation-buttons">
          <button 
            className="nav-button prev"
            onClick={navigateToPreviousQuestion}
            disabled={currentQuestionIndex === 0}
          >
            Previous Question
          </button>
          
          <button 
            className="nav-button next"
            onClick={navigateToNextQuestion}
          >
            {currentQuestionIndex === testData.questions.length - 1 
              ? "Finish Test" 
              : "Next Question"
            }
          </button>
        </div>

        <DebugPanel />
      </div>
    </div>
  );
}

export default TestPage;