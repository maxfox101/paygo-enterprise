from typing import Dict, Any, Optional
from dataclasses import dataclass
import httpx
import json
import uuid
from datetime import datetime

from config import settings
from models.transaction import Transaction, PaymentMethod, BankAcquirer

@dataclass
class PaymentResult:
    success: bool
    bank_transaction_id: Optional[str] = None
    bank_response: Optional[str] = None
    card_mask: Optional[str] = None
    receipt_number: Optional[str] = None
    error_message: Optional[str] = None

class PaymentProcessor:
    """Класс для обработки платежей через различные банки"""
    
    def __init__(self):
        self.timeout = 30.0
    
    async def process_payment(self, transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
        """Главный метод обработки платежа"""
        
        try:
            # Выбор процессора в зависимости от метода оплаты
            if transaction.payment_method == PaymentMethod.QR_CODE:
                return await self._process_sbp_payment(transaction, payment_data)
            
            elif transaction.payment_method in [PaymentMethod.NFC_CARD, PaymentMethod.NFC_PHONE]:
                return await self._process_card_payment(transaction, payment_data)
            
            elif transaction.payment_method in [PaymentMethod.BIOMETRY_FACE, PaymentMethod.BIOMETRY_FINGERPRINT]:
                return await self._process_biometry_payment(transaction, payment_data)
            
            else:
                return PaymentResult(
                    success=False,
                    error_message="Неподдерживаемый метод оплаты"
                )
                
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=f"Ошибка обработки платежа: {str(e)}"
            )
    
    async def _process_sbp_payment(self, transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
        """Обработка платежа через СБП (QR код)"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Подготовка данных для СБП
                sbp_request = {
                    "merchant_id": settings.SBP_MERCHANT_ID,
                    "amount": transaction.amount,
                    "currency": "RUB",
                    "order_id": transaction.transaction_id,
                    "qr_id": payment_data.get("qr_id"),
                    "customer_phone": payment_data.get("phone"),
                    "description": transaction.description or "Оплата через терминал PayGo"
                }
                
                # Отправка запроса в СБП
                response = await client.post(
                    f"{settings.SBP_API_URL}/payment",
                    json=sbp_request,
                    headers={
                        "Authorization": f"Bearer {settings.SBP_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("status") == "success":
                    return PaymentResult(
                        success=True,
                        bank_transaction_id=response_data.get("transaction_id"),
                        bank_response=json.dumps(response_data),
                        receipt_number=response_data.get("receipt_number"),
                        card_mask=response_data.get("card_mask")  # СБП может вернуть маску карты
                    )
                else:
                    return PaymentResult(
                        success=False,
                        bank_response=json.dumps(response_data),
                        error_message=response_data.get("message", "Ошибка СБП")
                    )
                    
        except httpx.TimeoutException:
            return PaymentResult(
                success=False,
                error_message="Таймаут при обращении к СБП"
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=f"Ошибка СБП: {str(e)}"
            )
    
    async def _process_card_payment(self, transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
        """Обработка платежа по карте (NFC)"""
        
        # Определение банка по BIN карты
        card_number = payment_data.get("card_number")
        if not card_number:
            return PaymentResult(
                success=False,
                error_message="Отсутствует номер карты"
            )
        
        # Определяем банк-эквайер
        bank_acquirer = self._determine_acquirer(card_number)
        
        if bank_acquirer == BankAcquirer.VTB:
            return await self._process_vtb_payment(transaction, payment_data)
        elif bank_acquirer == BankAcquirer.ALFABANK:
            return await self._process_alfa_payment(transaction, payment_data)
        elif bank_acquirer == BankAcquirer.CENTRINVEST:
            return await self._process_centrinvest_payment(transaction, payment_data)
        else:
            # Дефолтный эквайер
            return await self._process_vtb_payment(transaction, payment_data)
    
    async def _process_vtb_payment(self, transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
        """Обработка платежа через ВТБ"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                vtb_request = {
                    "merchant_id": settings.VTB_MERCHANT_ID,
                    "amount": int(transaction.amount * 100),  # В копейках
                    "currency": "RUB",
                    "order_id": transaction.transaction_id,
                    "card_data": {
                        "pan": payment_data["card_number"],
                        "exp_month": payment_data.get("exp_month"),
                        "exp_year": payment_data.get("exp_year"),
                        "cvv": payment_data.get("cvv")
                    },
                    "description": transaction.description or "Оплата через терминал PayGo"
                }
                
                response = await client.post(
                    f"{settings.VTB_API_URL}/payment",
                    json=vtb_request,
                    headers={
                        "Authorization": f"Bearer {settings.VTB_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("status") == "approved":
                    return PaymentResult(
                        success=True,
                        bank_transaction_id=response_data.get("transaction_id"),
                        bank_response=json.dumps(response_data),
                        card_mask=self._mask_card_number(payment_data["card_number"]),
                        receipt_number=f"VTB{response_data.get('receipt_id', '')}"
                    )
                else:
                    return PaymentResult(
                        success=False,
                        bank_response=json.dumps(response_data),
                        error_message=response_data.get("message", "Отклонено ВТБ")
                    )
                    
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=f"Ошибка ВТБ: {str(e)}"
            )
    
    async def _process_alfa_payment(self, transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
        """Обработка платежа через Альфа-Банк"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                alfa_request = {
                    "merchantId": settings.ALFA_MERCHANT_ID,
                    "amount": int(transaction.amount * 100),
                    "currency": "643",  # RUB
                    "orderNumber": transaction.transaction_id,
                    "pan": payment_data["card_number"],
                    "expiry": f"{payment_data.get('exp_month', ''):02d}{payment_data.get('exp_year', '')[-2:]}",
                    "cvc": payment_data.get("cvv"),
                    "description": transaction.description or "Оплата PayGo"
                }
                
                response = await client.post(
                    f"{settings.ALFA_API_URL}/rest/payment.do",
                    data=alfa_request,
                    headers={
                        "Authorization": f"Bearer {settings.ALFA_API_KEY}"
                    }
                )
                
                response_data = response.json()
                
                if response_data.get("errorCode") == "0":
                    return PaymentResult(
                        success=True,
                        bank_transaction_id=response_data.get("orderId"),
                        bank_response=json.dumps(response_data),
                        card_mask=self._mask_card_number(payment_data["card_number"]),
                        receipt_number=f"ALFA{response_data.get('orderId', '')}"
                    )
                else:
                    return PaymentResult(
                        success=False,
                        bank_response=json.dumps(response_data),
                        error_message=response_data.get("errorMessage", "Отклонено Альфа-Банком")
                    )
                    
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=f"Ошибка Альфа-Банка: {str(e)}"
            )
    
    async def _process_centrinvest_payment(self, transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
        """Обработка платежа через Центр-Инвест"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                ci_request = {
                    "merchant_id": settings.CENTRINVEST_MERCHANT_ID,
                    "amount": transaction.amount,
                    "currency": "RUB",
                    "transaction_id": transaction.transaction_id,
                    "card": {
                        "number": payment_data["card_number"],
                        "expiry_month": payment_data.get("exp_month"),
                        "expiry_year": payment_data.get("exp_year"),
                        "cvv": payment_data.get("cvv")
                    }
                }
                
                response = await client.post(
                    f"{settings.CENTRINVEST_API_URL}/api/payment",
                    json=ci_request,
                    headers={
                        "X-API-Key": settings.CENTRINVEST_API_KEY,
                        "Content-Type": "application/json"
                    }
                )
                
                response_data = response.json()
                
                if response_data.get("result") == "success":
                    return PaymentResult(
                        success=True,
                        bank_transaction_id=response_data.get("id"),
                        bank_response=json.dumps(response_data),
                        card_mask=self._mask_card_number(payment_data["card_number"]),
                        receipt_number=f"CI{response_data.get('receipt', '')}"
                    )
                else:
                    return PaymentResult(
                        success=False,
                        bank_response=json.dumps(response_data),
                        error_message=response_data.get("error", "Отклонено Центр-Инвестом")
                    )
                    
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=f"Ошибка Центр-Инвеста: {str(e)}"
            )
    
    async def _process_biometry_payment(self, transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
        """Обработка биометрического платежа"""
        
        try:
            # Верификация биометрических данных
            biometry_verified = await self._verify_biometry(
                transaction.user_id,
                payment_data.get("biometry_template"),
                transaction.payment_method
            )
            
            if not biometry_verified:
                return PaymentResult(
                    success=False,
                    error_message="Биометрическая верификация не пройдена"
                )
            
            # Получение основной карты пользователя
            from database import SessionLocal
            from models.card import Card
            
            db = SessionLocal()
            try:
                user_card = db.query(Card).filter(
                    Card.user_id == transaction.user_id,
                    Card.is_primary == True,
                    Card.is_active == True
                ).first()
                
                if not user_card:
                    return PaymentResult(
                        success=False,
                        error_message="Не найдена активная карта для биометрического платежа"
                    )
                
                # Обработка как обычный карточный платеж
                card_payment_data = {
                    "card_token": user_card.card_token,  # Используем токен вместо номера
                    "card_mask": user_card.card_mask
                }
                
                # В реальной системе здесь был бы запрос к банку с использованием токена
                return PaymentResult(
                    success=True,
                    bank_transaction_id=f"BIO_{uuid.uuid4().hex[:8]}",
                    bank_response=json.dumps({"status": "approved", "method": "biometry"}),
                    card_mask=user_card.card_mask,
                    receipt_number=f"BIO{int(datetime.utcnow().timestamp())}"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            return PaymentResult(
                success=False,
                error_message=f"Ошибка биометрического платежа: {str(e)}"
            )
    
    def _determine_acquirer(self, card_number: str) -> BankAcquirer:
        """Определение банка-эквайера по BIN карты"""
        
        bin_number = card_number[:6]
        
        # Примерные BIN коды (в реальной системе используется актуальная база BIN)
        vtb_bins = ["427200", "427201", "427202"]
        alfa_bins = ["548673", "548674", "415482"]
        centrinvest_bins = ["533174", "533175"]
        
        if bin_number in vtb_bins:
            return BankAcquirer.VTB
        elif bin_number in alfa_bins:
            return BankAcquirer.ALFABANK
        elif bin_number in centrinvest_bins:
            return BankAcquirer.CENTRINVEST
        else:
            return BankAcquirer.VTB  # Дефолтный эквайер
    
    def _mask_card_number(self, card_number: str) -> str:
        """Маскировка номера карты"""
        
        if len(card_number) < 8:
            return "*" * len(card_number)
        
        return f"**** **** **** {card_number[-4:]}"
    
    async def _verify_biometry(self, user_id: Optional[int], biometry_template: str, method: PaymentMethod) -> bool:
        """Верификация биометрических данных"""
        
        if not user_id or not biometry_template:
            return False
        
        # В реальной системе здесь была бы верификация через биометрическую систему
        # Сравнение шаблона с сохраненными данными пользователя
        
        # Заглушка - всегда возвращаем True для демонстрации
        return True

# Создание глобального экземпляра процессора
processor = PaymentProcessor()

async def process_payment(transaction: Transaction, payment_data: Dict[str, Any]) -> PaymentResult:
    """Функция-обертка для обработки платежа"""
    return await processor.process_payment(transaction, payment_data) 