import React from 'react';

function Header() {
  return (
    <header style={{
      backgroundColor: '#1976d2',
      padding: '1rem',
      color: '#fff',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <h1>Socratic: Practice Exam</h1>
      <nav>
        <a href="#" style={{ color: '#fff', marginRight: '1rem' }}>Home</a>
        <a href="#" style={{ color: '#fff', marginRight: '1rem' }}>About</a>
        <a href="#" style={{ color: '#fff' }}>Profile</a>
      </nav>
    </header>
  );
}

export default Header;
