import React, { useState } from 'react';
import './Cards.css';

const Cards = () => {
  const [cards] = useState([
    {
      id: 1,
      bank: 'Т-банк',
      type: 'Дебетовая',
      number: '•••• 5678',
      balance: 128456.32,
      expiry: '04/27',
      gradient: 'linear-gradient(135deg, #f7931e, #ff6b35)',
    },
    {
      id: 2,
      bank: 'ВТБ',
      type: 'Дебетовая',
      number: '•••• 1234',
      balance: 45321.90,
      expiry: '08/26',
      gradient: 'linear-gradient(135deg, #1e3a8a, #3b82f6)',
    },
    {
      id: 3,
      bank: 'Альфа-банк',
      type: 'Кредитная',
      number: '•••• 9876',
      balance: 19079.21,
      expiry: '11/25',
      gradient: 'linear-gradient(135deg, #dc2626, #ef4444)',
    },
  ]);

  const [showAddCard, setShowAddCard] = useState(false);

  const handleAddCard = () => {
    setShowAddCard(true);
  };

  const handleCloseModal = () => {
    setShowAddCard(false);
  };

  return (
    <div className="cards-page">
      <div className="cards-grid">
        {cards.map(card => (
          <div key={card.id} className="bank-card" style={{ background: card.gradient }}>
            <div className="card-header">
              <div>
                <div className="bank-name">{card.bank}</div>
                <div className="card-type">{card.type}</div>
              </div>
              <div className="card-expiry">{card.expiry}</div>
            </div>
            <div className="card-number">{card.number}</div>
            <div className="card-balance">{card.balance.toLocaleString('ru-RU')} ₽</div>
          </div>
        ))}
        
        <button className="add-card-button card" onClick={handleAddCard}>
          <div className="add-icon">+</div>
          <div className="add-text">Добавить карту</div>
        </button>
      </div>

      {/* Card Management Features */}
      <div className="card-features">
        <div className="feature-section card">
          <h3>💳 Управление картами</h3>
          <div className="feature-list">
            <div className="feature-item">
              <div className="feature-icon">🔗</div>
              <div>
                <div className="feature-title">Привязка карт</div>
                <div className="feature-desc">Добавляйте карты любых российских банков</div>
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">⚙️</div>
              <div>
                <div className="feature-title">Настройка платежей</div>
                <div className="feature-desc">Выберите основную карту для оплат</div>
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔒</div>
              <div>
                <div className="feature-title">Безопасность</div>
                <div className="feature-desc">Все данные карт надежно зашифрованы</div>
              </div>
            </div>
          </div>
        </div>

        <div className="feature-section card">
          <h3>📊 Статистика использования</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">3</div>
              <div className="stat-label">Активных карт</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">47</div>
              <div className="stat-label">Операций в месяц</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">₽ 23,450</div>
              <div className="stat-label">Средний оборот</div>
            </div>
          </div>
        </div>
      </div>

      {/* Add Card Modal */}
      {showAddCard && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Добавить новую карту</h3>
              <button className="close-button" onClick={handleCloseModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Номер карты</label>
                <input type="text" placeholder="0000 0000 0000 0000" maxLength="19" />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Месяц/Год</label>
                  <input type="text" placeholder="MM/YY" maxLength="5" />
                </div>
                <div className="form-group">
                  <label>CVV</label>
                  <input type="text" placeholder="000" maxLength="3" />
                </div>
              </div>
              <div className="form-group">
                <label>Имя держателя</label>
                <input type="text" placeholder="NIKITA ZOSIM" />
              </div>
              <div className="modal-actions">
                <button className="btn btn-secondary" onClick={handleCloseModal}>
                  Отмена
                </button>
                <button className="btn btn-primary">
                  Добавить карту
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cards; 