import React from 'react';
import { useAuth } from '../context/AuthContext';
import './Header.css';

const Header = ({ currentPage }) => {
  const { user } = useAuth();
  
  const pageConfig = {
    dashboard: {
      greeting: 'Пятница, 8 августа 2025 г.',
      title: 'Здравствуйте, Никита!',
      showBalance: true
    },
    cards: {
      greeting: 'Управление картами',
      title: 'Мои карты',
      showBalance: false
    },
    support: {
      greeting: 'Нужна помощь?',
      title: 'Поддержка',
      showBalance: false
    },
    profile: {
      greeting: 'Личные данные',
      title: 'Профиль',
      showBalance: false
    }
  };

  const config = pageConfig[currentPage] || pageConfig.dashboard;

  return (
    <div className="header">
      <div>
        <div className="greeting">{config.greeting}</div>
        <h1 className="page-title">{config.title}</h1>
      </div>
      {config.showBalance && (
        <div className="user-info">
          <div className="balance">
            <div className="balance-amount">192 857.43 ₽</div>
            <div className="balance-label">Общий баланс</div>
          </div>
        </div>
      )}
      {currentPage === 'cards' && (
        <button className="btn btn-primary">+ Добавить карту</button>
      )}
    </div>
  );
};

export default Header; 