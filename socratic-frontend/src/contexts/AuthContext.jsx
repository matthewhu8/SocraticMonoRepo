import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check for stored tokens when the app loads
    const checkAuth = async () => {
      const accessToken = localStorage.getItem('accessToken');
      const userType = localStorage.getItem('userType');
      const userName = localStorage.getItem('userName');
      
      if (accessToken) {
        try {
          // Create a simple authenticated user state
          setCurrentUser({
            userType,
            name: userName || 'User',
            isAuthenticated: true
          });
        } catch (error) {
          console.error('Auth check error:', error);
          setError(error.message);
          // In case of error, clear tokens
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('userType');
          localStorage.removeItem('userName');
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const refreshToken = async () => {
    // For now, just implement a simplified version
    return false;
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userType');
    localStorage.removeItem('userName');
    setCurrentUser(null);
  };

  return (
    <AuthContext.Provider 
      value={{ 
        currentUser, 
        loading, 
        error, 
        logout, 
        refreshToken, 
        setCurrentUser 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider; 