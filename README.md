# GAX - Production-Grade Digital Banking + Payment Gateway Platform

A complete, production-ready digital banking and payment gateway system built for Nigeria, featuring wallet management, bill payments, and merchant integration capabilities.

## 🚀 Features

### Core Banking
- **User Management** - Registration, authentication (JWT), KYC verification
- **Wallet System** - Multi-currency wallets with balance and ledger tracking
- **Transactions** - Deposits, withdrawals, transfers with atomic operations
- **Bank Accounts** - Link external bank accounts for withdrawals

### Payment Gateway
- **Merchant Integration** - Easy API for websites to accept payments
- **Payment Links** - Generate secure payment URLs
- **Webhooks** - Real-time payment notifications
- **API Keys** - Secure merchant authentication (test & live modes)

### Bill Payments
- **Airtime** - MTN, Glo, Airtel, 9Mobile
- **Data Bundles** - All major network providers
- **TV Subscriptions** - DSTV, GOtv, Startimes
- **Electricity** - PHED, IKEDC, AEDC, EEDC, EKEDC

### Moniepoint Integration
- Virtual account creation
- Transaction verification
- Bank transfers
- Webhook handling with signature verification
- Automatic settlement

### Security
- UUID-based primary keys (no sequential IDs)
- JWT authentication
- API key authentication for merchants
- Transaction PIN validation
- AES-256 encryption for sensitive data
- HMAC signature verification for webhooks
- Rate limiting (DRF throttling)
- CSRF protection
- Atomic database transactions

## 📋 Requirements

- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- Django 5.0+
- Django REST Framework

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/awaaladin/gax.git
cd gax
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Database setup
```bash
# Create PostgreSQL database
createdb gax_banking

# Run migrations
python manage.py makemigrations accounts
python manage.py migrate
```

### 6. Create superuser
```bash
python manage.py createsuperuser
```

### 7. Run development server
```bash
python manage.py runserver
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all required environment variables:

- **Django**: SECRET_KEY, DEBUG, ALLOWED_HOSTS
- **Database**: PostgreSQL connection details
- **Redis**: Cache and Celery broker
- **Moniepoint**: API credentials (sandbox & live)
- **Payment APIs**: Bill payment provider credentials

### Moniepoint Setup

1. Register at [Moniepoint](https://moniepoint.com)
2. Get API credentials (sandbox for testing, live for production)
3. Add credentials to `.env`:
   ```
   MONIEPOINT_SANDBOX_API_KEY=your-key
   MONIEPOINT_SANDBOX_SECRET_KEY=your-secret
   MONIEPOINT_SANDBOX_CONTRACT_CODE=your-code
   ```

## 📚 API Documentation

### Authentication

#### Register User
```http
POST /api/auth/register/
Content-Type: application/json

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

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Set Transaction PIN
```http
POST /api/auth/set-pin/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "pin": "1234",
  "confirm_pin": "1234"
}
```

### Wallet Operations

#### Get Wallet
```http
GET /api/wallets/
Authorization: Bearer <access-token>
```

#### Deposit
```http
POST /api/wallet/deposit/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "amount": "5000.00",
  "description": "Wallet funding"
}
```

#### Transfer
```http
POST /api/wallet/transfer/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "amount": "1000.00",
  "recipient_account": "2012345678",
  "transaction_pin": "1234",
  "narration": "Payment for services"
}
```

#### Withdraw
```http
POST /api/wallet/withdraw/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "amount": "5000.00",
  "bank_account_id": "uuid-here",
  "transaction_pin": "1234"
}
```

### Bill Payments

#### Buy Airtime
```http
POST /api/bills/airtime/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "provider": "mtn",
  "phone_number": "08012345678",
  "amount": "500.00",
  "transaction_pin": "1234"
}
```

#### Buy Data
```http
POST /api/bills/data/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "provider": "mtn",
  "phone_number": "08012345678",
  "plan_code": "MTN-1GB-30",
  "transaction_pin": "1234"
}
```

#### Pay for TV
```http
POST /api/bills/tv/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "provider": "dstv",
  "smartcard_number": "1234567890",
  "plan_code": "DSTV-COMPACT",
  "transaction_pin": "1234"
}
```

#### Pay for Electricity
```http
POST /api/bills/electricity/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "provider": "ikedc",
  "meter_number": "12345678901",
  "meter_type": "prepaid",
  "amount": "5000.00",
  "transaction_pin": "1234"
}
```

### Payment Gateway (Merchant Integration)

#### Initiate Payment
```http
POST /api/payments/initiate/
X-API-Key: sk_live_your-api-key
Content-Type: application/json

{
  "amount": "10000.00",
  "email": "customer@example.com",
  "customer_name": "Jane Doe",
  "callback_url": "https://yourwebsite.com/callback"
}

Response:
{
  "success": true,
  "payment_url": "https://gax.com/pay/PAY-ABC123",
  "reference": "PAY-ABC123",
  "amount": "10000.00",
  "fee": "150.00",
  "merchant_amount": "9850.00"
}
```

#### Verify Payment
```http
POST /api/payments/verify/
X-API-Key: sk_live_your-api-key
Content-Type: application/json

{
  "reference": "PAY-ABC123"
}
```

#### Check Payment Status
```http
GET /api/payments/status/PAY-ABC123/
```

## 🔗 Webhook Integration

### Moniepoint Webhook
```http
POST /api/webhooks/moniepoint/
X-Moniepoint-Signature: signature-here
Content-Type: application/json

{
  "eventType": "SUCCESSFUL_TRANSACTION",
  "transactionReference": "TXN-123456",
  "amount": 10000.00,
  ...
}
```

The system automatically:
- Verifies webhook signature
- Logs webhook in database
- Updates payment status
- Credits merchant wallet
- Sends callback to merchant

## 🔐 Security Best Practices

1. **Never expose SECRET_KEY** - Keep it in environment variables
2. **Use HTTPS in production** - Enable SSL redirect in settings
3. **Rotate API keys** - Especially if compromised
4. **Monitor webhook logs** - Check for suspicious activity
5. **Enable rate limiting** - Prevent abuse
6. **Validate all inputs** - Serializers handle this
7. **Use transaction pins** - For sensitive operations
8. **Implement 2FA** - For admin accounts

## 📊 Database Schema

### Core Models
- **User** - Custom user with UUIDs, phone verification
- **Profile** - User profile with KYC info
- **Wallet** - Account number, balance, ledger balance
- **BankAccount** - External bank account linking
- **Transaction** - All financial transactions
- **BillPayment** - Bill payment records
- **PaymentGateway** - Merchant payment records
- **APIKey** - Merchant API authentication
- **WebhookLog** - Webhook audit trail
- **KYC** - Know Your Customer verification

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL
- [ ] Set up Redis
- [ ] Configure proper `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS`
- [ ] Enable SSL (`SECURE_SSL_REDIRECT=True`)
- [ ] Configure email backend
- [ ] Set up Sentry for error tracking
- [ ] Configure AWS S3 for media files
- [ ] Set up Celery workers
- [ ] Configure domain and CORS
- [ ] Test all payment integrations
- [ ] Set up monitoring and logging

### Using Gunicorn
```bash
gunicorn gax.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Using Docker
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "gax.wsgi:application"]
```

## 🧪 Testing

```bash
# Run tests
python manage.py test

# With coverage
pytest --cov=banking

# Specific test
python manage.py test banking.accounts.tests.test_payments
```

## 🛠️ Management Commands

### Reconcile Transactions
```bash
python manage.py reconcile_transactions --hours 24
```

### Process Settlements
```bash
python manage.py process_settlements --limit 100
```

## 📝 License

This project is proprietary software. All rights reserved.

## 👥 Support

For support, email: support@gaxbank.com

## 🙏 Acknowledgments

- Moniepoint API
- Django & DRF communities
- Nigerian fintech ecosystem
