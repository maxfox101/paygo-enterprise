import React, { useState } from 'react';
import './Support.css';

const Support = () => {
  const [activeFaq, setActiveFaq] = useState(null);

  const supportOptions = [
    {
      icon: '💬',
      title: 'Чат с поддержкой',
      desc: 'Получите помощь в режиме реального времени',
      action: 'Начать чат',
      color: 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
    },
    {
      icon: '📞',
      title: 'Звонок в банк',
      desc: '8-988-898-60-02',
      action: 'Позвонить',
      color: 'linear-gradient(135deg, #10b981, #059669)'
    },
    {
      icon: '✉️',
      title: 'Электронная почта',
      desc: 'Отправьте свой вопрос нам на почту',
      action: 'Написать письмо',
      color: 'linear-gradient(135deg, #f59e0b, #d97706)'
    }
  ];

  const faqItems = [
    {
      question: 'Как добавить новую карту?',
      answer: 'Для добавления новой карты перейдите в раздел "Мои карты" и нажмите кнопку "Добавить карту". Следуйте инструкциям на экране для ввода данных карты.'
    },
    {
      question: 'Как сменить пароль от личного кабинета?',
      answer: 'Перейдите в раздел "Профиль" → "Безопасность" и нажмите "Сменить пароль". Введите текущий пароль и новый пароль дважды.'
    },
    {
      question: 'Как настроить уведомления?',
      answer: 'В разделе "Профиль" → "Уведомления" вы можете настроить push-уведомления, SMS и email-уведомления по своему усмотрению.'
    },
    {
      question: 'Как работает биометрическая аутентификация?',
      answer: 'Биометрическая аутентификация использует отпечатки пальцев или распознавание лица для безопасного входа в приложение. Настроить её можно в разделе "Профиль" → "Безопасность".'
    },
    {
      question: 'Что делать, если терминал не работает?',
      answer: 'Если терминал не отвечает, попробуйте перезагрузить его. Если проблема не решается, обратитесь в техническую поддержку по телефону или через чат.'
    },
    {
      question: 'Как отследить статус платежа?',
      answer: 'Все ваши платежи отображаются в разделе "История". Там вы можете увидеть статус каждой транзакции и получить детальную информацию.'
    }
  ];

  const toggleFaq = (index) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  return (
    <div className="support-page">
      {/* Support Options */}
      <div className="support-options">
        {supportOptions.map((option, index) => (
          <div key={index} className="support-card card">
            <div className="support-icon" style={{ background: option.color }}>
              {option.icon}
            </div>
            <div className="support-title">{option.title}</div>
            <div className="support-desc">{option.desc}</div>
            <button className="btn btn-primary">{option.action}</button>
          </div>
        ))}
      </div>

      {/* FAQ Section */}
      <div className="faq-section">
        <h2 className="section-title">Частые вопросы</h2>
        <div className="faq-list">
          {faqItems.map((item, index) => (
            <div key={index} className={`faq-item ${activeFaq === index ? 'active' : ''}`}>
              <button 
                className="faq-question"
                onClick={() => toggleFaq(index)}
              >
                {item.question}
                <span className={`faq-arrow ${activeFaq === index ? 'active' : ''}`}>▼</span>
              </button>
              {activeFaq === index && (
                <div className="faq-answer">
                  {item.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Contact Info */}
      <div className="contact-info card">
        <h3>📞 Контактная информация</h3>
        <div className="contact-grid">
          <div className="contact-item">
            <div className="contact-label">Техническая поддержка:</div>
            <div className="contact-value">8-988-898-60-02</div>
          </div>
          <div className="contact-item">
            <div className="contact-label">Email:</div>
            <div className="contact-value">support@paygo.ru</div>
          </div>
          <div className="contact-item">
            <div className="contact-label">Время работы:</div>
            <div className="contact-value">24/7</div>
          </div>
          <div className="contact-item">
            <div className="contact-label">Адрес:</div>
            <div className="contact-value">г. Ростов-на-Дону, ул. Большая Садовая, 105</div>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="system-status card">
        <h3>🔧 Статус системы</h3>
        <div className="status-grid">
          <div className="status-item">
            <div className="status-indicator online"></div>
            <div className="status-info">
              <div className="status-name">API Сервер</div>
              <div className="status-value">Работает</div>
            </div>
          </div>
          <div className="status-item">
            <div className="status-indicator online"></div>
            <div className="status-info">
              <div className="status-name">База данных</div>
              <div className="status-value">Работает</div>
            </div>
          </div>
          <div className="status-item">
            <div className="status-indicator online"></div>
            <div className="status-info">
              <div className="status-name">Платежная система</div>
              <div className="status-value">Работает</div>
            </div>
          </div>
          <div className="status-item">
            <div className="status-indicator warning"></div>
            <div className="status-info">
              <div className="status-name">Терминалы</div>
              <div className="status-value">2 из 5 онлайн</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Support; 