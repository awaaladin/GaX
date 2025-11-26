# 🧪 TESTING GUIDE - GAX Banking Platform

Complete guide for testing all features of the GAX Banking Platform.

## Prerequisites

- Server running at `http://localhost:8000`
- PostgreSQL database configured
- Postman or curl installed
- Valid test data

---

## 1️⃣ User Registration & Authentication

### Register a New User
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

**Expected Response:**
```json
{
  "user": {
    "id": "uuid",
    "username": "testuser",
    "email": "test@example.com"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Registration successful"
}
```

**Save the access token for subsequent requests.**

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123"
  }'
```

### Set Transaction PIN
```bash
curl -X POST http://localhost:8000/api/auth/set-pin/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "pin": "1234",
    "confirm_pin": "1234"
  }'
```

---

## 2️⃣ Wallet Operations

### View Wallet
```bash
curl http://localhost:8000/api/wallets/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "account_number": "2012345678",
      "balance": "0.00",
      "ledger_balance": "0.00",
      "currency": "NGN",
      "is_active": true
    }
  ]
}
```

### Deposit Money
```bash
curl -X POST http://localhost:8000/api/wallet/deposit/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": "10000.00",
    "description": "Test deposit"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "transaction": {
    "reference": "TXN-ABC123456",
    "amount": "10000.00",
    "status": "completed"
  },
  "wallet": {
    "balance": "10000.00"
  },
  "message": "Deposit successful"
}
```

### Transfer Money

First, create a second user to transfer to, then:

```bash
curl -X POST http://localhost:8000/api/wallet/transfer/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": "500.00",
    "recipient_account": "2098765432",
    "transaction_pin": "1234",
    "narration": "Test transfer"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "transaction": {
    "reference": "TXN-DEF456789",
    "amount": "500.00",
    "fee": "10.00",
    "total_amount": "510.00",
    "status": "completed"
  },
  "message": "Transfer successful"
}
```

### Request Withdrawal

First, add a bank account in Django admin, then:

```bash
curl -X POST http://localhost:8000/api/wallet/withdraw/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": "1000.00",
    "bank_account_id": "bank-account-uuid",
    "transaction_pin": "1234",
    "description": "Test withdrawal"
  }'
```

---

## 3️⃣ Bill Payments

### Buy Airtime
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

**Expected Response:**
```json
{
  "success": true,
  "bill_payment": {
    "id": "uuid",
    "reference": "BILL-ABC123",
    "provider": "mtn",
    "amount": "500.00",
    "status": "completed"
  },
  "message": "Airtime purchase successful"
}
```

### Buy Data Bundle
```bash
curl -X POST http://localhost:8000/api/bills/data/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "provider": "mtn",
    "phone_number": "08012345678",
    "plan_code": "MTN-1GB-30",
    "transaction_pin": "1234"
  }'
```

### Pay for TV Subscription
```bash
curl -X POST http://localhost:8000/api/bills/tv/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "provider": "dstv",
    "smartcard_number": "1234567890",
    "plan_code": "DSTV-COMPACT",
    "transaction_pin": "1234"
  }'
```

### Pay for Electricity
```bash
curl -X POST http://localhost:8000/api/bills/electricity/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "provider": "ikedc",
    "meter_number": "12345678901",
    "meter_type": "prepaid",
    "amount": "5000.00",
    "transaction_pin": "1234"
  }'
```

**Expected Response includes token:**
```json
{
  "success": true,
  "bill_payment": {
    "reference": "BILL-XYZ789",
    "amount": "5000.00",
    "token": "1234-5678-9012-3456",
    "status": "completed"
  },
  "token": "1234-5678-9012-3456",
  "message": "Payment successful"
}
```

---

## 4️⃣ Payment Gateway (Merchant)

### Create API Key

First, upgrade user to merchant in Django admin, then:

```bash
curl -X POST http://localhost:8000/api/api-keys/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "environment": "test",
    "name": "My Test Key"
  }'
```

**Expected Response:**
```json
{
  "id": "uuid",
  "key": "sk_test_abc123...",
  "secret": "secret_xyz789...",
  "environment": "test",
  "is_active": true
}
```

**Save the API key for merchant requests.**

### Initiate Payment
```bash
curl -X POST http://localhost:8000/api/payments/initiate/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_test_abc123..." \
  -d '{
    "amount": "5000.00",
    "email": "customer@example.com",
    "customer_name": "Jane Doe",
    "callback_url": "https://yourwebsite.com/callback"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "payment_url": "http://localhost:8000/pay/PAY-ABC123",
  "reference": "PAY-ABC123",
  "amount": "5000.00",
  "fee": "75.00",
  "merchant_amount": "4925.00"
}
```

### Verify Payment
```bash
curl -X POST http://localhost:8000/api/payments/verify/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_test_abc123..." \
  -d '{
    "reference": "PAY-ABC123"
  }'
```

### Check Payment Status (Public)
```bash
curl http://localhost:8000/api/payments/status/PAY-ABC123/
```

---

## 5️⃣ Transaction History

### List All Transactions
```bash
curl http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Filter Transactions
```bash
# By type
curl "http://localhost:8000/api/transactions/?transaction_type=transfer" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# By status
curl "http://localhost:8000/api/transactions/?status=completed" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Newest first
curl "http://localhost:8000/api/transactions/?ordering=-created_at" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 6️⃣ Admin Operations

### View Dashboard Stats

Login as admin user, then:

```bash
curl http://localhost:8000/api/admin/dashboard/stats/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Approve Withdrawal
```bash
curl -X POST http://localhost:8000/api/admin/transactions/TRANSACTION_UUID/approve_withdrawal/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Reject Withdrawal
```bash
curl -X POST http://localhost:8000/api/admin/transactions/TRANSACTION_UUID/reject_withdrawal/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -d '{
    "reason": "Insufficient documentation"
  }'
```

### Approve KYC
```bash
curl -X POST http://localhost:8000/api/admin/kyc/KYC_UUID/approve/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Freeze User Wallet
```bash
curl -X POST http://localhost:8000/api/admin/users/USER_UUID/freeze_wallet/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

---

## 7️⃣ Webhook Testing

### Simulate Moniepoint Webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/moniepoint/ \
  -H "Content-Type: application/json" \
  -H "X-Moniepoint-Signature: test-signature" \
  -d '{
    "eventType": "SUCCESSFUL_TRANSACTION",
    "transactionReference": "TXN-123456",
    "amount": 5000.00,
    "customerEmail": "customer@example.com",
    "status": "SUCCESSFUL"
  }'
```

---

## 🧪 Automated Testing

### Run Unit Tests
```bash
python manage.py test
```

### Run Specific Test
```bash
python manage.py test banking.accounts.tests.test_wallet
```

### With Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

---

## 📊 Load Testing

### Using Apache Bench
```bash
# Test deposit endpoint
ab -n 1000 -c 10 -T 'application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -p deposit.json \
  http://localhost:8000/api/wallet/deposit/
```

Where `deposit.json` contains:
```json
{"amount": "100.00", "description": "Load test"}
```

### Using Locust

Create `locustfile.py`:
```python
from locust import HttpUser, task, between

class BankingUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/auth/login/", json={
            "username": "testuser",
            "password": "SecurePass123"
        })
        self.token = response.json()["access"]
    
    @task
    def view_wallet(self):
        self.client.get("/api/wallets/", 
            headers={"Authorization": f"Bearer {self.token}"})
    
    @task(2)
    def view_transactions(self):
        self.client.get("/api/transactions/",
            headers={"Authorization": f"Bearer {self.token}"})
```

Run:
```bash
locust -f locustfile.py
```

---

## ✅ Test Checklist

### Registration & Auth
- [ ] User registration works
- [ ] Email validation works
- [ ] Phone number validation (Nigerian format)
- [ ] Password strength validation
- [ ] Login returns JWT tokens
- [ ] Token refresh works
- [ ] Transaction PIN can be set
- [ ] PIN must be 4 digits

### Wallet
- [ ] Wallet auto-created on registration
- [ ] Unique 10-digit account number
- [ ] Deposit increases balance
- [ ] Transfer debits sender, credits recipient
- [ ] Transfer fee calculated correctly
- [ ] Insufficient balance blocked
- [ ] Balance before/after recorded
- [ ] Concurrent transactions handled (F() expressions)

### Bill Payments
- [ ] Airtime purchase works for all providers
- [ ] Data purchase works with correct plans
- [ ] TV subscription validates smartcard
- [ ] Electricity payment validates meter
- [ ] Token returned for electricity
- [ ] Wallet debited correctly
- [ ] Failed payments reversed
- [ ] Transaction PIN verified

### Payment Gateway
- [ ] Merchants can create API keys
- [ ] Payment initiation works
- [ ] Payment URL generated
- [ ] Fee calculated correctly (1.5%, max ₦2000)
- [ ] Payment verification works
- [ ] Webhook signature verified
- [ ] Merchant wallet credited on success
- [ ] Callback URL called

### Security
- [ ] UUIDs used (no sequential IDs)
- [ ] JWT authentication works
- [ ] API key authentication works
- [ ] Transaction PIN required for sensitive ops
- [ ] Webhook signatures verified
- [ ] Rate limiting enforced
- [ ] CSRF protection enabled

### Admin
- [ ] Dashboard shows stats
- [ ] Withdrawals can be approved/rejected
- [ ] KYC can be approved/rejected
- [ ] Wallets can be frozen/unfrozen
- [ ] All transactions visible
- [ ] Webhook logs visible

---

## 🐛 Common Issues & Solutions

### Database Connection Error
```
Solution: Check PostgreSQL is running
sudo systemctl status postgresql
```

### Import Error
```
Solution: Activate virtual environment
source venv/bin/activate
```

### Migration Error
```
Solution: Reset migrations (dev only)
python manage.py migrate accounts zero
python manage.py makemigrations
python manage.py migrate
```

### Token Expired
```
Solution: Use refresh token to get new access token
```

### Insufficient Balance
```
Solution: Deposit more funds first
```

### Invalid PIN
```
Solution: Set transaction PIN via /api/auth/set-pin/
```

---

## 📝 Test Data

Use these test credentials:

**Networks:** mtn, glo, airtel, 9mobile
**TV Providers:** dstv, gotv, startimes
**Electricity:** phed, ikedc, aedc, eedc, ekedc

**Test Phone Numbers:** 08012345678, 08087654321
**Test Meter:** 12345678901
**Test Smartcard:** 1234567890

---

**Happy Testing! 🎉**
