import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

const Profile = () => {
  const { user, updateUser, logout } = useAuth();
  const [notifications, setNotifications] = useState({
    push: true,
    sms: true,
    email: false
  });

  const toggleNotification = (type) => {
    setNotifications(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="profile-page">
      {/* Profile Header */}
      <div className="profile-header card">
        <div className="avatar">НЗ</div>
        <div className="user-info">
          <h2 className="user-name">{user.name}</h2>
          <div className="user-meta">ID: {user.id}</div>
          <div className="user-meta">Клиент с {user.memberSince} года</div>
        </div>
        <button className="btn btn-secondary" onClick={handleLogout}>
          Выйти
        </button>
      </div>

      {/* Profile Sections */}
      <div className="profile-grid">
        <div className="profile-section card">
          <h3>
            <span className="section-icon">📝</span>
            Личные данные
          </h3>
          <div className="profile-fields">
            <div className="profile-field">
              <div className="field-label">ФИО:</div>
              <div className="field-value">{user.name}</div>
            </div>
            <div className="profile-field">
              <div className="field-label">Дата рождения:</div>
              <div className="field-value">29.06.2006</div>
            </div>
            <div className="profile-field">
              <div className="field-label">Телефон:</div>
              <div className="field-value">{user.phone}</div>
            </div>
            <div className="profile-field">
              <div className="field-label">Email:</div>
              <div className="field-value">{user.email}</div>
            </div>
          </div>
          <button className="btn btn-secondary">Редактировать</button>
        </div>

        <div className="profile-section card">
          <h3>
            <span className="section-icon">🔒</span>
            Безопасность
          </h3>
          <div className="profile-fields">
            <div className="profile-field">
              <div className="field-label">Пароль:</div>
              <div className="field-value">••••••••</div>
            </div>
            <div className="profile-field">
              <div className="field-label">Последний вход:</div>
              <div className="field-value">13.05.2025, 15:08</div>
            </div>
            <div className="profile-field">
              <div className="field-label">Двухфакторная аутентификация:</div>
              <div className="field-value security-enabled">Включена ✓</div>
            </div>
          </div>
          <button className="btn btn-secondary">Сменить пароль</button>
        </div>

        <div className="profile-section card">
          <h3>
            <span className="section-icon">🔔</span>
            Уведомления
          </h3>
          <div className="notification-settings">
            <div className="notification-item">
              <span>Push-уведомления</span>
              <div 
                className={`toggle-switch ${notifications.push ? 'active' : ''}`}
                onClick={() => toggleNotification('push')}
              >
                <div className="switch-handle"></div>
              </div>
            </div>
            <div className="notification-item">
              <span>SMS-уведомления</span>
              <div 
                className={`toggle-switch ${notifications.sms ? 'active' : ''}`}
                onClick={() => toggleNotification('sms')}
              >
                <div className="switch-handle"></div>
              </div>
            </div>
            <div className="notification-item">
              <span>Email-уведомления</span>
              <div 
                className={`toggle-switch ${notifications.email ? 'active' : ''}`}
                onClick={() => toggleNotification('email')}
              >
                <div className="switch-handle"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Account Stats */}
      <div className="account-stats card">
        <h3>📊 Статистика аккаунта</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">💳</div>
            <div className="stat-value">3</div>
            <div className="stat-label">Активных карт</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💸</div>
            <div className="stat-value">47</div>
            <div className="stat-label">Транзакций за месяц</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🏪</div>
            <div className="stat-value">12</div>
            <div className="stat-label">Посещенных терминалов</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⭐</div>
            <div className="stat-value">4.8</div>
            <div className="stat-label">Рейтинг клиента</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="recent-activity card">
        <h3>📈 Последняя активность</h3>
        <div className="activity-list">
          <div className="activity-item">
            <div className="activity-icon">💳</div>
            <div className="activity-info">
              <div className="activity-title">Добавлена карта ВТБ</div>
              <div className="activity-time">2 дня назад</div>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">🔒</div>
            <div className="activity-info">
              <div className="activity-title">Изменены настройки безопасности</div>
              <div className="activity-time">1 неделю назад</div>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">💸</div>
            <div className="activity-info">
              <div className="activity-title">Оплата в терминале №7</div>
              <div className="activity-time">2 недели назад</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile; 