import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './Login.css';

const Login = () => {
  const { login, loading } = useAuth();
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const result = await login(credentials);
    if (!result.success) {
      setError(result.error);
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <div className="logo">
            <div className="logo-icon">PG</div>
            <div className="logo-text">PayGo</div>
          </div>
          <h1>Добро пожаловать</h1>
          <p>Войдите в свой аккаунт PayGo</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label>Email или телефон</label>
            <input
              type="text"
              name="email"
              value={credentials.email}
              onChange={handleChange}
              placeholder="nzosim@sfedu.ru"
              required
            />
          </div>

          <div className="form-group">
            <label>Пароль</label>
            <input
              type="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
            />
          </div>

          <div className="form-options">
            <label className="checkbox-label">
              <input type="checkbox" />
              <span>Запомнить меня</span>
            </label>
            <a href="#" className="forgot-link">Забыли пароль?</a>
          </div>

          <button 
            type="submit" 
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>

          <div className="biometric-login">
            <div className="divider">
              <span>или</span>
            </div>
            <button type="button" className="biometric-button">
              <span className="biometric-icon">👆</span>
              Войти по отпечатку
            </button>
          </div>
        </form>

        <div className="login-footer">
          <p>Нет аккаунта? <a href="#" className="register-link">Зарегистрироваться</a></p>
        </div>
      </div>

      <div className="login-features">
        <div className="feature-card">
          <div className="feature-icon">💳</div>
          <h3>Управление картами</h3>
          <p>Добавляйте карты всех российских банков</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🔒</div>
          <h3>Безопасные платежи</h3>
          <p>Биометрия и двухфакторная аутентификация</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Аналитика</h3>
          <p>Отслеживайте все операции и терминалы</p>
        </div>
      </div>
    </div>
  );
};

export default Login; 