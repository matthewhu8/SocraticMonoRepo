import React, { useState, useEffect, useMemo, useRef } from 'react';
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
  const [messages, setMessages] = useState({});
  const [answers, setAnswers] = useState({});
  const [testCompleted, setTestCompleted] = useState(false);
  const [questionResults, setQuestionResults] = useState({});
  const [testStartTime, setTestStartTime] = useState(null);
  const [testResultsModalOpen, setTestResultsModalOpen] = useState(false);
  const [testResults, setTestResults] = useState(null);

  // Memoize key values used across multiple useEffects to maintain referential stability
  const memoizedQuestionResults = useMemo(() => questionResults, [JSON.stringify(questionResults)]);
  const memoizedTestData = useMemo(() => testData, [testData?.id, testData?.questions?.length]);

  // Fetch test data when component mounts
  useEffect(() => {
    const fetchTest = async () => {
      try {
        console.log(`Attempting to fetch test with code: ${testCode}`);
        setLoading(true);
        
        const userId = '30'; // Convert to string to match backend expectations
        const response = await fetch(`http://127.0.0.1:8000/tests/${testCode}?user_id=${userId}`);
        
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
        
        // Set test start time when test is loaded
        const startTime = new Date().toISOString();
        setTestStartTime(startTime);
        
        // Initialize the first question's start time
        setQuestionResults(prev => ({
          ...prev,
          0: {
            ...(prev[0] || {}),
            startTime: startTime
          }
        }));
      } catch (error) {
        console.error('Error fetching test:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTest();
  }, [testCode]);

  // Initialize test tracking when test data is loaded
  useEffect(() => {
    if (memoizedTestData && !testStartTime) {
      setTestStartTime(new Date());
      
      // Check if question results are already initialized to prevent re-initialization
      const areResultsInitialized = Object.keys(memoizedQuestionResults).length > 0;
      
      if (!areResultsInitialized) {
        // Initialize question results
        const initialResults = {};
        memoizedTestData.questions.forEach((_, index) => {
          initialResults[index] = {
            startTime: new Date(),
            endTime: null,
            answer: null,
            isCorrect: false,
            timeSpent: 0,
            attempts: 0,
            messages: []
          };
        });
        setQuestionResults(initialResults);
      }
    }
  // Use memoized values in dependency array
  }, [memoizedTestData, testStartTime, memoizedQuestionResults]);

  // Update question tracking when navigating questions
  useEffect(() => {
    // Only run this effect when we have valid data
    if (memoizedTestData && memoizedQuestionResults && memoizedQuestionResults[currentQuestionIndex]) {
      // Add testData check and avoid calling setQuestionResults if not needed
      const prevTimeSpent = memoizedQuestionResults[currentQuestionIndex].timeSpent || 0;
      const newTimeSpent = (new Date() - new Date(memoizedQuestionResults[currentQuestionIndex].startTime)) / 1000;
      
      // Only update if the time spent has meaningfully changed
      if (Math.abs(newTimeSpent - prevTimeSpent) > 1) {
        setQuestionResults(prev => ({
          ...prev,
          [currentQuestionIndex]: {
            ...prev[currentQuestionIndex],
            endTime: new Date(),
            timeSpent: newTimeSpent
          }
        }));
      }
    }
  // Use memoized values in dependency array
  }, [currentQuestionIndex, memoizedQuestionResults, memoizedTestData]);

  // Use useMemo to compute currentQuestion only when dependencies change
  const currentQuestion = useMemo(() => {
    if (!memoizedTestData || !memoizedTestData.questions || memoizedTestData.questions.length === 0) {
      return null;
    }
    
    const question = memoizedTestData.questions[currentQuestionIndex];
    
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
  }, [memoizedTestData, currentQuestionIndex]);
  
  const handleSendMessage = async (text) => {
    const questionId = currentQuestionIndex;
    
    // Update message history
    setQuestionResults(prev => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        messages: [...(prev[questionId]?.messages || []), { sender: 'student', content: text }]
      }
    }));
    
    // Add user message to chat
    const userMessage = { sender: 'User', text };
    setMessages(prev => ({
      ...prev,
      [questionId]: [...(prev[questionId] || []), userMessage]
    }));
  
    try {
      // Check if this is an answer submission - ONLY if it contains both "answer" AND a number
      const isAnswerKeyword = text.toLowerCase().includes("answer");
      const numberMatch = text.match(/\b\d+(\.\d+)?\b/);
      
      // Only process as an answer submission if BOTH conditions are met
      if (isAnswerKeyword && numberMatch) {
        const answerValue = numberMatch[0];
        
        setQuestionResults(prev => ({
          ...prev,
          [questionId]: {
            ...prev[questionId],
            answer: answerValue,
            attempts: (prev[questionId]?.attempts || 0) + 1
          }
        }));
        
        setAnswers(prev => ({
          ...prev,
          [questionId]: answerValue
        }));
        
        // Submit the answer to the backend for validation
        await submitAnswer(answerValue, questionId);
        
        // Skip chat query for answer submissions
        return;
      }
      
      // Continue with chat query for all non-answer submissions
      const chatPayload = {
        test_id: testData.id,
        test_code: testCode,
        question_id: currentQuestion.id,
        public_question: currentQuestion.public_question,
        query: text,
        user_id: '30',
        isPracticeExam: testData.isPracticeExam || false
      };
      
      console.log("Sending chat data to backend:", chatPayload);
      
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(chatPayload),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Update message history with AI response
      setQuestionResults(prev => ({
        ...prev,
        [questionId]: {
          ...prev[questionId],
          messages: [...(prev[questionId]?.messages || []), { sender: 'ai', content: data.response }]
        }
      }));
      
      const aiMessage = { sender: 'AI', text: data.response };
      setMessages(prev => ({
        ...prev,
        [questionId]: [...(prev[questionId] || []), aiMessage]
      }));
      
      // Remove AI confirmation logic - rely solely on direct answer submissions

    } catch (error) {
      console.error('Error fetching AI response:', error);
      const errorMessage = { sender: 'System', text: 'Error: Unable to get response from AI.' };
      setMessages(prev => ({
        ...prev,
        [questionId]: [...(prev[questionId] || []), errorMessage]
      }));
    }
  };

  // Function to submit an answer to the backend for validation
  const submitAnswer = async (answer, questionIndex) => {
    try {
      const submission = {
        user_id: '30', // Use string user ID for consistency
        test_code: testCode,
        question_id: testData.questions[questionIndex].id,
        question_index: questionIndex,
        answer: answer
      };

      const response = await fetch('http://127.0.0.1:8000/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submission)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Update the question result with the validated answer
      setQuestionResults(prev => ({
        ...prev,
        [questionIndex]: {
          ...prev[questionIndex],
          isCorrect: data.is_correct,
          validatedAnswer: true
        }
      }));

      // Show appropriate message based on answer validation
      if (data.is_correct) {
        const correctMessage = { sender: 'System', text: 'Correct answer! Well done.' };
        setMessages(prev => ({
          ...prev,
          [questionIndex]: [...(prev[questionIndex] || []), correctMessage]
        }));
      } else {
        const incorrectMessage = { sender: 'System', text: 'Incorrect answer. Try again!' };
        setMessages(prev => ({
          ...prev,
          [questionIndex]: [...(prev[questionIndex] || []), incorrectMessage]
        }));
      }

      return data;
    } catch (error) {
      console.error('Error submitting answer:', error);
      // Don't show an error message to the user, as this is a background operation
      return null;
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

  const submitTest = async () => {
    try {
      setLoading(true);
      
      // Mark the current question as ended
      if (currentQuestionIndex >= 0 && questionResults[currentQuestionIndex]) {
        const endTime = new Date().toISOString();
        setQuestionResults(prev => ({
          ...prev,
          [currentQuestionIndex]: {
            ...(prev[currentQuestionIndex] || {}),
            endTime: endTime
          }
        }));
      }
      
      // Call the backend finish-test endpoint
      const finishTestPayload = {
        user_id: '30', // Convert to string as expected by the backend
        test_id: testData.id,
        test_code: testCode
      };
      
      console.log("Submitting test with payload:", finishTestPayload);
      
      const response = await fetch('http://127.0.0.1:8000/finish-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finishTestPayload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Failed to submit test results: ${response.status} ${response.statusText}`);
        console.error(`Error details: ${errorText}`);
        throw new Error(`Failed to submit test results: ${response.statusText}`);
      }

      const resultData = await response.json();
      console.log("Test submission response:", resultData);
      
      // Prepare the full test results with all details
      const processedResults = {
        test_id: resultData.test_id || testData.id,
        id: resultData.id,
        score: resultData.score || 0,
        correct_answers: resultData.correct_answers || 0,
        total_questions: resultData.total_questions || testData.questions.length,
        total_time: resultData.total_time || 0,
        start_time: resultData.start_time || testStartTime,
        end_time: resultData.end_time || new Date().toISOString()
      };
      
      setTestResults(processedResults);
      
      // Show the test results modal automatically
      setTestResultsModalOpen(true);
      setLoading(false);
      
      // Set a timeout to automatically redirect to dashboard after 10 seconds
      // This gives the user time to view their results but ensures they get back to dashboard
      setTimeout(() => {
        if (document.visibilityState === 'visible') {
          navigate('/student');
        }
      }, 10000);
    } catch (error) {
      setLoading(false);
      console.error('Error submitting test:', error);
      alert('Failed to submit test results. Please try again.');
    }
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

  // Test Results Modal Component
  const TestResultModal = ({ isOpen, onClose, results }) => {
    if (!isOpen || !results) return null;
    
    // Safely extract values with fallbacks to prevent undefined errors
    const score = results.score || 0;
    const correctAnswers = results.correct_answers || 0;
    const totalQuestions = results.total_questions || 0;
    const totalTime = results.total_time || 0;
    
    // Format time into hours, minutes, seconds
    const hours = Math.floor(totalTime / 3600);
    const minutes = Math.floor((totalTime % 3600) / 60);
    const seconds = Math.floor(totalTime % 60);
    const formattedTime = hours > 0 
      ? `${hours}h ${minutes}m ${seconds}s` 
      : `${minutes}m ${seconds}s`;
    
    // Function to handle closing the modal and navigating
    const handleClose = () => {
      onClose();
    };
    
    return (
      <div className="modal-overlay">
        <div className="modal-content results-modal">
          <div className="results-header">
            <h2>Test Results Summary</h2>
          </div>
          
          <div className="results-container">
            <div className="score-section">
              <div className="score-circle">
                <div className="score-value">{Math.round(score)}%</div>
              </div>
              <div className="score-details">
                <div className="score-item">
                  <span className="score-label">Correct Answers:</span>
                  <span className="score-data">{correctAnswers} of {totalQuestions}</span>
                </div>
                <div className="score-item">
                  <span className="score-label">Time Spent:</span>
                  <span className="score-data">{formattedTime}</span>
                </div>
                <div className="score-item">
                  <span className="score-label">Started:</span>
                  <span className="score-data">{new Date(results.start_time).toLocaleString()}</span>
                </div>
                <div className="score-item">
                  <span className="score-label">Finished:</span>
                  <span className="score-data">{new Date(results.end_time).toLocaleString()}</span>
                </div>
              </div>
            </div>
            
            <div className="questions-section">
              <h3>Your Answers</h3>
              <div className="questions-container">
                {testData.questions.map((question, index) => {
                  const isCorrect = questionResults[index]?.isCorrect;
                  const userAnswer = answers[index] || "Not answered";
                  const timeSpent = questionResults[index]?.timeSpent || 0;
                  const mins = Math.floor(timeSpent / 60);
                  const secs = Math.floor(timeSpent % 60);
                  
                  return (
                    <div key={index} className={`question-result ${isCorrect ? 'correct' : 'incorrect'}`}>
                      <div className="question-number">
                        <span className="number">{index + 1}</span>
                        <span className={`status-icon ${isCorrect ? 'correct' : 'incorrect'}`}>
                          {isCorrect ? '✓' : '✗'}
                        </span>
                      </div>
                      <div className="question-content">
                        <p className="question-text">{question.public_question || question.publicQuestion}</p>
                        <div className="answer-details">
                          <p className="your-answer">
                            <strong>Your answer:</strong> {userAnswer}
                          </p>
                          <p className="time-spent">
                            <strong>Time spent:</strong> {mins}m {secs}s
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          
          <div className="modal-footer">
            <button className="primary-button" onClick={handleClose}>
              Return to Dashboard
            </button>
            <button className="secondary-button" onClick={handleClose}>
              Close
            </button>
          </div>
        </div>
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
    // Function to handle test results modal closing
    const handleTestResultsClose = () => {
      setTestResultsModalOpen(false);
      navigate('/student');
    };
    
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
          <h2>{testData.name || testData.test_name}</h2>
          
          {testResultsModalOpen ? (
            <div className="submission-status success">
              <div className="status-icon">✓</div>
              <p>Test successfully submitted!</p>
              <p className="status-message">Viewing test results...</p>
            </div>
          ) : (
            <>
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
                      <p>
                        <strong>Your answer:</strong> {answers[index] || "Not answered"}
                        {questionResults[index]?.validatedAnswer && (
                          questionResults[index]?.isCorrect ? 
                          <span className="correct-indicator"> ✓ Correct</span> : 
                          <span className="incorrect-indicator"> ✗ Incorrect</span>
                        )}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="test-actions">
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
                  Return to Questions
                </button>
              </div>
            </>
          )}
        </div>
        
        {/* Test Results Modal */}
        <TestResultModal 
          isOpen={testResultsModalOpen} 
          onClose={handleTestResultsClose}
          results={testResults}
        />
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
          <h2>{testData?.name || testData?.test_name || 'Test'}</h2>
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
        <h1>{testData.name || testData.test_name}</h1>
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
            <div className={`answer-provided ${questionResults[currentQuestionIndex]?.isCorrect ? 'correct' : questionResults[currentQuestionIndex]?.validatedAnswer ? 'incorrect' : ''}`}>
              Your answer: {answers[currentQuestionIndex]}
              {questionResults[currentQuestionIndex]?.validatedAnswer && (
                questionResults[currentQuestionIndex]?.isCorrect ? 
                <span className="correct-indicator"> ✓ Correct</span> : 
                <span className="incorrect-indicator"> ✗ Incorrect</span>
              )}
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
      
      {/* Test Results Modal */}
      <TestResultModal 
        isOpen={testResultsModalOpen} 
        onClose={() => {
          setTestResultsModalOpen(false);
          navigate('/student');
        }}
        results={testResults}
      />
    </div>
  );
}

function QuestionSection({ question, onAnswer, isAnswered }) {
  return (
    <div className="question-section">
      <h3>Question {question.question_number}</h3>
      <p>{question.question_text}</p>
      {question.image_url && (
        <div className="question-image">
          <img 
            src={question.image_url} 
            alt="Question" 
            style={{ maxWidth: '100%', marginTop: '10px' }} 
          />
        </div>
      )}
      {/* ... rest of the question section ... */}
    </div>
  );
}

export default TestPage;