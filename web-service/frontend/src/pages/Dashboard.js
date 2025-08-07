import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const [currencyRates, setCurrencyRates] = useState([
    { symbol: '$', name: 'USD', rate: '91.45 ₽', change: '-0.23%', positive: false },
    { symbol: '€', name: 'EUR', rate: '98.72 ₽', change: '+0.15%', positive: true },
    { symbol: '¥', name: 'CNY', rate: '12.63 ₽', change: '+0.42%', positive: true },
  ]);

  const quickActions = [
    { icon: '🔄', title: 'Перевод', desc: 'Быстрый перевод средств', color: 'linear-gradient(135deg, #ff6b35, #f7931e)' },
    { icon: '💳', title: 'Платежи', desc: 'Оплата услуг и товаров', color: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' },
    { icon: '📊', title: 'История', desc: 'Просмотр операций', color: 'linear-gradient(135deg, #10b981, #059669)' },
    { icon: '⭐', title: 'Избранное', desc: 'Быстрый доступ', color: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
  ];

  const projectPlan = [
    { stage: 'Исследование', tasks: 'Анализ рынка, выбор форм-фактора, сбор требований', period: 'апрель 2025', status: 'completed' },
    { stage: 'Проектирование', tasks: 'Архитектура терминала и веб-сервиса', period: 'май 2025', status: 'completed' },
    { stage: 'Разработка прототипа', tasks: 'Реализация ПО терминала (frontend + backend)', period: 'июнь – август 2025', status: 'current' },
    { stage: 'Разработка веб-сервиса', tasks: 'Сайт, личный кабинет, система управления картами', period: 'июль – сентябрь 2025', status: 'current' },
    { stage: 'Интеграция', tasks: 'Работа с API банков (ВТБ, Альфа, Центр-Инвест и др.)', period: 'сентябрь – октябрь 2025', status: 'planned' },
    { stage: 'Тестирование', tasks: 'Безопасность, функционал, UX, подготовка к защите', period: 'октябрь 2025', status: 'planned' },
    { stage: 'Презентация', tasks: 'Защита проекта', period: 'конец октября 2025', status: 'planned' },
  ];

  const terminalFeatures = [
    { title: '💳 Способы оплаты', items: ['NFC (карты, телефоны)', 'QR-коды', 'Биометрия (лицо, отпечаток)'] },
    { title: '🏦 Интеграция с банками', items: ['Поддержка всех банков РФ', 'СБП и эквайринг', 'Фискальные регистраторы', 'Отправка данных в налоговую'] },
    { title: '⚙️ Дополнительные возможности', items: ['Офлайн-режим', 'Автоматические обновления', 'Удалённый мониторинг', 'Диагностика'] },
  ];

  const webServiceFeatures = [
    { title: '💳 Управление картами', items: ['Привязка банковских карт любого банка', 'Настройка способов оплаты', 'Выбор основной карты'] },
    { title: '🔒 Биометрия и безопасность', items: ['Добавление биометрических шаблонов', 'Двухфакторная аутентификация', 'Безопасное хранение данных'] },
    { title: '📊 Мониторинг и управление', items: ['История оплат', 'Состояние терминалов', 'Панель администратора', 'Управление устройствами'] },
  ];

  const terminalTech = [
    { title: 'Основные языки', desc: 'C++ / Python (RPi.GPIO, OpenCV, pySerial)' },
    { title: 'Графический интерфейс', desc: 'Qt (C++ или PyQt/PySide для Python)' },
    { title: 'Биометрия', desc: 'OpenCV, dlib (Python)' },
    { title: 'API и обмен данными', desc: 'requests, aiohttp, httpx (Python)' },
    { title: 'Локальное хранение', desc: 'SQLite / JSON-файлы' },
    { title: 'Платформа', desc: 'Raspberry Pi 4 / Orange Pi (ARM64, Linux)' },
  ];

  const webTech = [
    { title: 'Backend', desc: 'Python (FastAPI) ИЛИ Node.js' },
    { title: 'Frontend', desc: 'JavaScript + React' },
    { title: 'Безопасность', desc: 'JWT, OAuth2, HTTPS, OpenID Connect' },
    { title: 'API банков', desc: 'REST API + Webhooks' },
    { title: 'База данных', desc: 'JSON-файлы → PostgreSQL (при расширении)' },
    { title: 'Хостинг', desc: 'Docker + VPS / Render / Railway / Yandex Cloud' },
    { title: 'Биометрия в вебе', desc: 'WebRTC + WebAssembly' },
  ];

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return <span className="status-completed">✅ Завершено</span>;
      case 'current': return <span className="status-current">🔄 В процессе</span>;
      case 'planned': return <span className="status-planned">📅 Запланировано</span>;
      default: return status;
    }
  };

  return (
    <div className="dashboard">
      {/* Currency Exchange */}
      <div className="currency-card card">
        <div className="card-header">
          <div className="card-icon" style={{ background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' }}>💱</div>
          <div className="card-title">Курсы валют</div>
        </div>
        <div className="currency-list">
          {currencyRates.map((currency, index) => (
            <div key={index} className="currency-item">
              <div className="currency-info">
                <span className="currency-symbol" style={{ color: '#3b82f6' }}>{currency.symbol}</span>
                <span className="currency-name">{currency.name}</span>
              </div>
              <div className="currency-rate">
                <div className="rate-value">{currency.rate}</div>
                <div className={`rate-change ${currency.positive ? 'positive' : 'negative'}`}>
                  {currency.positive ? '↑' : '↓'} {currency.change}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions grid grid-4">
        {quickActions.map((action, index) => (
          <button key={index} className="action-card card">
            <div className="action-icon" style={{ background: action.color }}>
              {action.icon}
            </div>
            <div className="action-title">{action.title}</div>
            <div className="action-desc">{action.desc}</div>
          </button>
        ))}
      </div>

      {/* Project Plan */}
      <div className="plan-table card">
        <div className="table-header">
          <h2 className="table-title">📋 План работ по созданию продукта</h2>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Этап</th>
                <th>Содержание работ</th>
                <th>Сроки</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {projectPlan.map((item, index) => (
                <tr key={index}>
                  <td>{item.stage}</td>
                  <td>{item.tasks}</td>
                  <td>{item.period}</td>
                  <td>{getStatusLabel(item.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Functionality */}
      <div className="functionality-section">
        <h2 className="section-title">🚀 Функциональность будущего продукта</h2>
        
        <div className="subsection">
          <h3 className="subsection-title">А. Терминал оплаты:</h3>
          <div className="feature-cards grid grid-3">
            {terminalFeatures.map((feature, index) => (
              <div key={index} className="feature-card card">
                <h4>{feature.title}</h4>
                <ul>
                  {feature.items.map((item, itemIndex) => (
                    <li key={itemIndex}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="subsection">
          <h3 className="subsection-title">Б. Веб-сервис (по типу Сбербанк Онлайн):</h3>
          <div className="feature-cards grid grid-3">
            {webServiceFeatures.map((feature, index) => (
              <div key={index} className="feature-card card">
                <h4>{feature.title}</h4>
                <ul>
                  {feature.items.map((item, itemIndex) => (
                    <li key={itemIndex}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Technologies */}
      <div className="tech-section">
        <h2 className="section-title">🛠️ Перечень технологий</h2>
        
        <div className="subsection">
          <h3 className="subsection-title">А. Для терминала (встроенное ПО + GUI)</h3>
          <div className="tech-cards grid grid-3">
            {terminalTech.map((tech, index) => (
              <div key={index} className="tech-card card">
                <h4>{tech.title}</h4>
                <p>{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="subsection">
          <h3 className="subsection-title">Б. Для веб-сервиса (сайт + веб-приложение)</h3>
          <div className="tech-cards grid grid-3">
            {webTech.map((tech, index) => (
              <div key={index} className="tech-card card">
                <h4>{tech.title}</h4>
                <p>{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 