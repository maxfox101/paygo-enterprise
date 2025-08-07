import React from 'react';
import './Sidebar.css';

const Sidebar = ({ currentPage, setCurrentPage }) => {
  const menuItems = [
    { id: 'dashboard', icon: '🏠', label: 'Главная' },
    { id: 'cards', icon: '💳', label: 'Мои карты' },
    { id: 'support', icon: '🛠️', label: 'Поддержка' },
    { id: 'profile', icon: '👤', label: 'Профиль' },
  ];

  return (
    <div className="sidebar">
      <div className="logo">
        <div className="logo-icon">PG</div>
        <div className="logo-text">PayGo</div>
      </div>
      
      <nav className="nav-menu">
        {menuItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
            onClick={() => setCurrentPage(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar; 