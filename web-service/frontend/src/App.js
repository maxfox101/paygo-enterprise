import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Cards from './pages/Cards';
import Support from './pages/Support';
import Profile from './pages/Profile';
import Login from './pages/Login';

// Context
import { AuthProvider, useAuth } from './context/AuthContext';

function AppContent() {
  const { isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState('dashboard');

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="app">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <div className="main-content">
        <Header currentPage={currentPage} />
        <div className="content">
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'cards' && <Cards />}
          {currentPage === 'support' && <Support />}
          {currentPage === 'profile' && <Profile />}
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App; 