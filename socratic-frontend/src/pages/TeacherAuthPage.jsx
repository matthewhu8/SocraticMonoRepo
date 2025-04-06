import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/AuthPage.css';
import { AuthContext } from '../contexts/AuthContext';

function TeacherAuthPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    subject: '',
    school: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { setCurrentUser } = useContext(AuthContext);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      if (isSignUp) {
        // Registration process
        if (formData.password !== formData.confirmPassword) {
          setError('Passwords do not match');
          setIsLoading(false);
          return;
        }
        
        console.log("Attempting to register with:", formData.email);
        const registerResponse = await fetch('http://localhost:8000/api/auth/teacher/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: formData.name,
            email: formData.email,
            password: formData.password,
            subject: formData.subject,
            school: formData.school
          }),
        });
        
        console.log("Registration response status:", registerResponse.status);
        if (!registerResponse.ok) {
          const errorData = await registerResponse.json();
          console.error("Registration error:", errorData);
          throw new Error(errorData.detail || 'Registration failed');
        }
        
        // After successful registration, automatically log in
        await loginUser(formData.email, formData.password);
      } else {
        // Login process
        await loginUser(formData.email, formData.password);
      }
    } catch (error) {
      console.error("Authentication error:", error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const loginUser = async (email, password) => {
    try {
      console.log("Attempting login with:", email);
      const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      
      console.log("Login response status:", loginResponse.status);
      if (!loginResponse.ok) {
        const errorData = await loginResponse.json();
        console.error("Login error:", errorData);
        throw new Error(errorData.detail || 'Login failed');
      }
      
      const loginData = await loginResponse.json();
      console.log("Login successful, received tokens:", !!loginData.access_token);
      
      // Store tokens in localStorage
      localStorage.setItem('accessToken', loginData.access_token);
      localStorage.setItem('refreshToken', loginData.refresh_token);
      localStorage.setItem('userType', 'teacher');
      
      // If signing up, store the name from the form
      if (isSignUp) {
        localStorage.setItem('userName', formData.name);
      } else {
        // For existing users, we could fetch the profile, but for now we'll use a default or stored name
        // We'll get the actual name once we implement fetching profiles
        const storedName = localStorage.getItem('userName');
        if (!storedName) {
          // We don't have the name for existing users, so use email as fallback
          const username = email.split('@')[0];
          localStorage.setItem('userName', username);
        }
      }
      
      // Set a simplified user object in the AuthContext
      setCurrentUser({
        userType: 'teacher',
        name: isSignUp ? formData.name : (localStorage.getItem('userName') || email.split('@')[0]),
        isAuthenticated: true
      });
      
      console.log("Redirecting to dashboard");
      // Redirect to dashboard
      navigate('/teachers/dashboard');
    } catch (error) {
      console.error("Login function error:", error);
      throw error;
    }
  };

  const toggleForm = () => {
    setIsSignUp(!isSignUp);
    setError('');
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <Link to="/" className="back-link">← Back to Home</Link>
          <h1>{isSignUp ? 'Teacher Sign Up' : 'Teacher Sign In'}</h1>
          <p>{isSignUp ? 'Create your teacher account' : 'Access your teacher dashboard'}</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          {isSignUp && (
            <>
              <div className="form-group">
                <label htmlFor="name">Full Name</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Enter your full name"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="subject">Subject</label>
                <select
                  id="subject"
                  name="subject"
                  value={formData.subject}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Select your subject</option>
                  <option value="Business Management">Business Management</option>
                  <option value="Physics">Physics</option>
                  <option value="Mathematics">Mathematics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Biology">Biology</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="school">School Name</label>
                <input
                  type="text"
                  id="school"
                  name="school"
                  value={formData.school}
                  onChange={handleInputChange}
                  placeholder="Enter your school name"
                  required
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              required
            />
          </div>

          {isSignUp && (
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="Confirm your password"
                required
              />
            </div>
          )}

          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : (isSignUp ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isSignUp
              ? 'Already have an account?'
              : "Don't have an account yet?"}
            <button className="toggle-form-btn" onClick={toggleForm}>
              {isSignUp ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default TeacherAuthPage; 