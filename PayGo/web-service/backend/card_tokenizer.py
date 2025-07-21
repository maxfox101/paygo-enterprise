import hashlib
import secrets
from typing import Dict
from datetime import datetime

# В реальной системе токены должны храниться в отдельной PCI DSS compliant системе
# Это упрощенная демонстрационная версия

class CardTokenizer:
    """Класс для токенизации номеров банковских карт"""
    
    def __init__(self):
        # В реальной системе ключ должен храниться в HSM или защищенном хранилище
        self.encryption_key = "DEMO_KEY_CHANGE_IN_PRODUCTION"
    
    def tokenize_card(self, card_number: str) -> str:
        """Создание токена для номера карты"""
        
        # Очистка номера карты
        clean_card = card_number.replace(' ', '').replace('-', '')
        
        # Создание уникального токена
        timestamp = str(int(datetime.utcnow().timestamp()))
        random_part = secrets.token_hex(8)
        
        # Хеш от номера карты + соль
        card_hash = hashlib.sha256(
            f"{clean_card}{self.encryption_key}{timestamp}".encode()
        ).hexdigest()[:16]
        
        # Формирование токена
        token = f"TKN_{card_hash}_{random_part}"
        
        return token
    
    def generate_card_mask(self, card_number: str) -> str:
        """Генерация маски номера карты"""
        
        clean_card = card_number.replace(' ', '').replace('-', '')
        
        if len(clean_card) < 8:
            return "*" * len(clean_card)
        
        # Стандартная маска: показываем первые 4 и последние 4 цифры
        return f"{clean_card[:4]} **** **** {clean_card[-4:]}"
    
    def detect_payment_system(self, card_number: str) -> str:
        """Определение платежной системы по номеру карты"""
        
        clean_card = card_number.replace(' ', '').replace('-', '')
        
        if not clean_card:
            return "unknown"
        
        first_digit = clean_card[0]
        first_two = clean_card[:2] if len(clean_card) >= 2 else clean_card
        first_four = clean_card[:4] if len(clean_card) >= 4 else clean_card
        
        # Visa
        if first_digit == '4':
            return "visa"
        
        # Mastercard
        elif first_digit == '5' or first_two in ['22', '23', '24', '25', '26', '27']:
            return "mastercard"
        
        # МИР
        elif first_four in ['2200', '2201', '2202', '2203', '2204']:
            return "mir"
        
        # American Express
        elif first_two in ['34', '37']:
            return "amex"
        
        # UnionPay
        elif first_digit == '6' and len(clean_card) >= 16:
            return "unionpay"
        
        else:
            return "unknown"
    
    def detect_card_type(self, card_number: str) -> str:
        """Определение типа карты (приближенно, в реальности нужна база BIN)"""
        
        # В реальной системе здесь был бы запрос к базе BIN кодов
        # Пока возвращаем дефолтное значение
        return "debit"
    
    def detect_bank_issuer(self, card_number: str) -> str:
        """Определение банка-эмитента по BIN коду"""
        
        clean_card = card_number.replace(' ', '').replace('-', '')
        bin_code = clean_card[:6] if len(clean_card) >= 6 else clean_card
        
        # Примерная база BIN кодов (в реальной системе используется актуальная база)
        bin_database = {
            # Сбербанк
            "427600": "sberbank", "427601": "sberbank", "427602": "sberbank",
            "546938": "sberbank", "639002": "sberbank",
            
            # ВТБ
            "427200": "vtb", "427201": "vtb", "427202": "vtb",
            "531301": "vtb",
            
            # Альфа-Банк
            "548673": "alfabank", "548674": "alfabank", "415482": "alfabank",
            "458111": "alfabank",
            
            # Газпромбанк
            "427644": "gazprombank", "427645": "gazprombank",
            "533130": "gazprombank",
            
            # Тинькофф
            "437772": "tinkoff", "521324": "tinkoff",
            "428906": "tinkoff",
            
            # Центр-Инвест
            "533174": "centrinvest", "533175": "centrinvest"
        }
        
        return bin_database.get(bin_code, "other")
    
    def validate_card_number(self, card_number: str) -> bool:
        """Валидация номера карты по алгоритму Луна"""
        
        clean_card = card_number.replace(' ', '').replace('-', '')
        
        if not clean_card.isdigit() or len(clean_card) < 13 or len(clean_card) > 19:
            return False
        
        # Алгоритм Луна
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            
            return checksum % 10
        
        return luhn_checksum(clean_card) == 0

# Создание глобального экземпляра токенизатора
tokenizer = CardTokenizer()

def tokenize_card(card_number: str) -> str:
    """Функция-обертка для токенизации карты"""
    return tokenizer.tokenize_card(card_number)

def generate_card_mask(card_number: str) -> str:
    """Функция-обертка для генерации маски карты"""
    return tokenizer.generate_card_mask(card_number)

def get_card_info(card_number: str) -> Dict[str, str]:
    """Получение полной информации о карте"""
    
    return {
        "payment_system": tokenizer.detect_payment_system(card_number),
        "card_type": tokenizer.detect_card_type(card_number),
        "bank_issuer": tokenizer.detect_bank_issuer(card_number),
        "is_valid": tokenizer.validate_card_number(card_number)
    } 