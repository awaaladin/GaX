# GAX Banking Platform - API Endpoints Reference

Base URL: `http://localhost:8000/api/`

## 🔐 Authentication

### Register
**POST** `/auth/register/`

Request:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "phone_number": "08012345678",
  "first_name": "John",
  "last_name": "Doe"
}
```

Response:
```json
{
  "user": {
    "id": "uuid",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Registration successful"
}
```

### Login
**POST** `/auth/login/`

Request:
```json
{
  "username": "johndoe",
  "password": "SecurePass123"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
**POST** `/auth/refresh/`

Request:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Set Transaction PIN
**POST** `/auth/set-pin/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "pin": "1234",
  "confirm_pin": "1234"
}
```

---

## 💰 Wallet Operations

### Get Wallet
**GET** `/wallets/`
Headers: `Authorization: Bearer <token>`

Response:
```json
{
  "results": [
    {
      "id": "uuid",
      "username": "johndoe",
      "account_number": "2012345678",
      "balance": "10000.00",
      "ledger_balance": "10000.00",
      "currency": "NGN",
      "is_active": true,
      "is_frozen": false
    }
  ]
}
```

### Deposit
**POST** `/wallet/deposit/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "amount": "5000.00",
  "description": "Wallet funding",
  "metadata": {}
}
```

Response:
```json
{
  "success": true,
  "transaction": {
    "id": "uuid",
    "reference": "TXN-ABC123456",
    "amount": "5000.00",
    "status": "completed"
  },
  "wallet": {
    "balance": "15000.00"
  },
  "message": "Deposit successful"
}
```

### Transfer
**POST** `/wallet/transfer/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "amount": "1000.00",
  "recipient_account": "2098765432",
  "transaction_pin": "1234",
  "narration": "Payment for services"
}
```

Response:
```json
{
  "success": true,
  "transaction": {
    "reference": "TXN-DEF456789",
    "amount": "1000.00",
    "fee": "10.00",
    "total_amount": "1010.00",
    "status": "completed"
  },
  "message": "Transfer successful"
}
```

### Withdraw
**POST** `/wallet/withdraw/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "amount": "5000.00",
  "bank_account_id": "uuid-of-bank-account",
  "transaction_pin": "1234",
  "description": "Withdrawal to bank"
}
```

---

## 📱 Bill Payments

### Buy Airtime
**POST** `/bills/airtime/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "provider": "mtn",
  "phone_number": "08012345678",
  "amount": "500.00",
  "transaction_pin": "1234"
}
```

Providers: `mtn`, `glo`, `airtel`, `9mobile`

### Buy Data
**POST** `/bills/data/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "provider": "mtn",
  "phone_number": "08012345678",
  "plan_code": "MTN-1GB-30",
  "transaction_pin": "1234"
}
```

### Pay for TV
**POST** `/bills/tv/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "provider": "dstv",
  "smartcard_number": "1234567890",
  "plan_code": "DSTV-COMPACT",
  "transaction_pin": "1234"
}
```

Providers: `dstv`, `gotv`, `startimes`

### Pay for Electricity
**POST** `/bills/electricity/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "provider": "ikedc",
  "meter_number": "12345678901",
  "meter_type": "prepaid",
  "amount": "5000.00",
  "transaction_pin": "1234"
}
```

Providers: `phed`, `ikedc`, `aedc`, `eedc`, `ekedc`
Meter Types: `prepaid`, `postpaid`

---

## 🏪 Payment Gateway (Merchants)

### Create API Key
**POST** `/api-keys/`
Headers: `Authorization: Bearer <token>`

Request:
```json
{
  "environment": "test",
  "name": "My Test Key"
}
```

Response:
```json
{
  "id": "uuid",
  "key": "sk_test_abc123...",
  "secret": "secret_xyz789...",
  "environment": "test",
  "is_active": true
}
```

### Initiate Payment
**POST** `/payments/initiate/`
Headers: `X-API-Key: sk_live_your-key`

Request:
```json
{
  "amount": "10000.00",
  "email": "customer@example.com",
  "customer_name": "Jane Doe",
  "customer_phone": "08012345678",
  "callback_url": "https://yourwebsite.com/callback",
  "metadata": {
    "order_id": "ORD-123"
  }
}
```

Response:
```json
{
  "success": true,
  "payment_url": "https://gax.com/pay/PAY-ABC123",
  "reference": "PAY-ABC123",
  "amount": "10000.00",
  "fee": "150.00",
  "merchant_amount": "9850.00"
}
```

### Verify Payment
**POST** `/payments/verify/`
Headers: `X-API-Key: sk_live_your-key`

Request:
```json
{
  "reference": "PAY-ABC123"
}
```

Response:
```json
{
  "success": true,
  "payment": {
    "reference": "PAY-ABC123",
    "amount": "10000.00",
    "status": "successful",
    "paid_at": "2024-01-15T10:30:00Z",
    "customer_email": "customer@example.com"
  }
}
```

### Get Payment Status (Public)
**GET** `/payments/status/{reference}/`

No authentication required

---

## 📊 Transactions

### List Transactions
**GET** `/transactions/`
Headers: `Authorization: Bearer <token>`

Query Parameters:
- `transaction_type`: filter by type
- `status`: filter by status
- `ordering`: `-created_at` (newest first)
- `page`: page number

Response:
```json
{
  "count": 100,
  "next": "url-to-next-page",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "reference": "TXN-ABC123",
      "transaction_type": "transfer",
      "amount": "1000.00",
      "fee": "10.00",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## 🔔 Webhooks

### Moniepoint Webhook
**POST** `/webhooks/moniepoint/`
Headers: `X-Moniepoint-Signature: hmac-signature`

Request (from Moniepoint):
```json
{
  "eventType": "SUCCESSFUL_TRANSACTION",
  "transactionReference": "TXN-123456",
  "amount": 10000.00,
  "customerEmail": "customer@example.com"
}
```

Response:
```json
{
  "success": true
}
```

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "message": "Invalid data",
  "errors": {
    "amount": ["This field is required"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "message": "An error occurred"
}
```

---

## 📝 Notes

- All amounts are in Naira (NGN)
- All timestamps are in UTC
- Rate limits apply (see throttling settings)
- Transaction PINs must be 4 digits
- Phone numbers must be valid Nigerian numbers
- UUIDs are used for all IDs (not sequential integers)
