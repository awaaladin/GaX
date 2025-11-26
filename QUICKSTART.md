# Quick Start Guide - GAX Banking Platform

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd gax
pip install -r requirements.txt
```

### Step 2: Set Up Database
```bash
# Create PostgreSQL database
createdb gax_banking

# Or using psql
psql -U postgres
CREATE DATABASE gax_banking;
\q
```

### Step 3: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env - minimum required:
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=gax_banking
DB_USER=postgres
DB_PASSWORD=your-password
```

### Step 4: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 6: Run Server
```bash
python manage.py runserver
```

Server will be running at `http://localhost:8000`

## 📱 Test the API

### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123",
    "phone_number": "08012345678",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123"
  }'
```

Save the `access` token from the response.

### 3. Set Transaction PIN
```bash
curl -X POST http://localhost:8000/api/auth/set-pin/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "pin": "1234",
    "confirm_pin": "1234"
  }'
```

### 4. Check Wallet
```bash
curl http://localhost:8000/api/wallets/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Fund Wallet (Test Deposit)
```bash
curl -X POST http://localhost:8000/api/wallet/deposit/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": "10000.00",
    "description": "Test deposit"
  }'
```

### 6. Buy Airtime
```bash
curl -X POST http://localhost:8000/api/bills/airtime/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "provider": "mtn",
    "phone_number": "08012345678",
    "amount": "500.00",
    "transaction_pin": "1234"
  }'
```

## 🔧 Common Issues

### Database Connection Error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Or on Windows, check services
```

### Migration Errors
```bash
# Reset migrations (development only!)
python manage.py migrate accounts zero
python manage.py makemigrations accounts
python manage.py migrate
```

### Import Errors
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

## 📊 Admin Panel

Access the Django admin at: `http://localhost:8000/admin`

Login with your superuser credentials to:
- View users and wallets
- Approve withdrawals
- View transactions
- Manage API keys

## 🧪 Run Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test banking.accounts
```

## 📝 Next Steps

1. Configure Moniepoint credentials for real payments
2. Set up Redis for caching
3. Configure bill payment provider APIs
4. Set up Celery for background tasks
5. Deploy to production

## 💡 Tips

- Keep DEBUG=True for development only
- Use PostgreSQL, not SQLite, even in development
- Test all payment flows in sandbox mode first
- Monitor logs for errors: `tail -f logs/django.log`
- Use Postman or Insomnia for API testing

## 🆘 Need Help?

- Check README.md for full documentation
- Review code comments
- Check Django logs
- Email: support@gaxbank.com
