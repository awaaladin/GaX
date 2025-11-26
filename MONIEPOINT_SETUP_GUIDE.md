# 🔐 MONIEPOINT API INTEGRATION GUIDE

## Step 1: Get Your Moniepoint API Credentials

### A. Access the Developer Portal
1. Go to: **https://developer.moniepoint.com/** or **https://developer.teamapt.com/**
2. **Sign up** or **Login** with your business email
3. Complete any required verification (KYC/business registration)

### B. Create Your Application
1. Once logged in, navigate to **"My Apps"** or **"Applications"**
2. Click **"Create New Application"** or **"Register App"**
3. Fill in:
   - App Name: `GAX Banking Platform`
   - App Description: `Digital Banking & Payment Gateway`
   - Callback URL: `http://127.0.0.1:8000/api/webhooks/moniepoint/`
   - Business/Merchant Code (if required)

### C. Get Your Credentials
After creating your app, you should see:

```
SANDBOX CREDENTIALS:
├─ Base URL: https://sandbox.moniepoint.com/api/v1
├─ API Key: MK_TEST_XXXXXXXXXXXXXXXXX
├─ Secret Key: sk_test_XXXXXXXXXXXXXXXXX
├─ Client ID: XXXXXXXXXXXX
└─ Contract Code: XXXXXXXXXX

LIVE CREDENTIALS (Production):
├─ Base URL: https://api.moniepoint.com/api/v1
├─ API Key: MK_LIVE_XXXXXXXXXXXXXXXXX
├─ Secret Key: sk_live_XXXXXXXXXXXXXXXXX
├─ Client ID: XXXXXXXXXXXX
└─ Contract Code: XXXXXXXXXX
```

---

## Step 2: Update Your .env File

Once you have the real credentials, replace the test values in your `.env` file:

### Current Location:
`C:\Users\awaje\Documents\jefferson\documents\GAX\.env`

### Update These Lines:

```env
# Moniepoint - Sandbox (REPLACE WITH YOUR ACTUAL CREDENTIALS)
MONIEPOINT_SANDBOX_BASE_URL=https://sandbox.moniepoint.com/api/v1
MONIEPOINT_SANDBOX_API_KEY=YOUR_ACTUAL_SANDBOX_API_KEY_HERE
MONIEPOINT_SANDBOX_SECRET_KEY=YOUR_ACTUAL_SANDBOX_SECRET_KEY_HERE
MONIEPOINT_SANDBOX_CONTRACT_CODE=YOUR_ACTUAL_CONTRACT_CODE_HERE
MONIEPOINT_SANDBOX_CLIENT_ID=YOUR_CLIENT_ID_HERE

# Moniepoint - Live (Production - USE ONLY WHEN READY)
MONIEPOINT_LIVE_BASE_URL=https://api.moniepoint.com/api/v1
MONIEPOINT_LIVE_API_KEY=YOUR_ACTUAL_LIVE_API_KEY_HERE
MONIEPOINT_LIVE_SECRET_KEY=YOUR_ACTUAL_LIVE_SECRET_KEY_HERE
MONIEPOINT_LIVE_CONTRACT_CODE=YOUR_ACTUAL_LIVE_CONTRACT_CODE_HERE
MONIEPOINT_LIVE_CLIENT_ID=YOUR_LIVE_CLIENT_ID_HERE
```

⚠️ **IMPORTANT**: 
- Start with **SANDBOX** credentials for testing
- Never commit the `.env` file to Git (it's already in `.gitignore`)
- Switch to **LIVE** credentials only when ready for production

---

## Step 3: Moniepoint API Endpoints

Based on Moniepoint's typical API structure, here are the common endpoints:

### **A. Virtual Account Creation**
```http
POST /api/v1/disbursements/single/virtual-account
```
**Purpose**: Create a virtual account for a customer to receive payments

**Request Body**:
```json
{
  "accountReference": "user-wallet-94273f78",
  "accountName": "Test User",
  "customerEmail": "test@example.com",
  "customerName": "Test User",
  "getAllAvailableBanks": false,
  "preferredBanks": ["035"]
}
```

**Response**:
```json
{
  "requestSuccessful": true,
  "responseMessage": "success",
  "responseCode": "0",
  "responseBody": {
    "accountReference": "user-wallet-94273f78",
    "accountName": "Test User",
    "customerEmail": "test@example.com",
    "customerName": "Test User",
    "accounts": [
      {
        "bankCode": "035",
        "bankName": "Wema Bank",
        "accountNumber": "7123456789",
        "accountName": "Test User"
      }
    ]
  }
}
```

### **B. Initiate Transfer**
```http
POST /api/v1/disbursements/single
```
**Purpose**: Send money to a bank account

**Request Body**:
```json
{
  "amount": 5000.00,
  "reference": "TXN-ABC123456",
  "narration": "Withdrawal",
  "destinationBankCode": "058",
  "destinationAccountNumber": "0123456789",
  "destinationAccountName": "Recipient Name",
  "sourceAccountNumber": "1234567890"
}
```

### **C. Verify Transaction**
```http
GET /api/v1/disbursements/single/validate?transactionReference={reference}
```
**Purpose**: Check transaction status

### **D. Webhook Notifications**
```http
POST /api/webhooks/moniepoint/
```
**Purpose**: Receive real-time payment notifications

**Webhook Payload**:
```json
{
  "eventType": "SUCCESSFUL_TRANSACTION",
  "transactionReference": "TXN-123456",
  "amount": 5000.00,
  "customerEmail": "customer@example.com",
  "status": "SUCCESSFUL",
  "paymentReference": "PAY-789012"
}
```

---

## Step 4: API Authentication

Moniepoint typically uses one of these methods:

### **Method 1: API Key Header**
```python
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
```

### **Method 2: HMAC Signature**
```python
import hmac
import hashlib

def generate_signature(payload, secret_key):
    message = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    return signature

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Signature": signature,
    "Content-Type": "application/json"
}
```

---

## Step 5: Testing Your Integration

### **Test with Sandbox**

1. **Start your server**:
```bash
cd C:\Users\awaje\Documents\jefferson\documents\GAX\gax\banking
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

2. **Test Virtual Account Creation**:
```bash
# Register a user
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Pass123!",
    "confirm_password": "Pass123!",
    "phone_number": "08012345678",
    "first_name": "Test",
    "last_name": "User"
  }'
```

3. **Check if virtual account was created** (if implemented in signals)

4. **Test Deposit** (via Moniepoint):
```bash
curl -X POST http://127.0.0.1:8000/api/wallet/deposit/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "5000.00",
    "description": "Test deposit via Moniepoint"
  }'
```

---

## Step 6: Common Moniepoint API Errors

### Error Codes:
- `99`: General failure - Check your credentials
- `01`: Invalid API key - Regenerate your API key
- `02`: Insufficient balance - Fund your Moniepoint account
- `03`: Invalid account number - Verify the account
- `04`: Transaction failed - Retry or contact support

---

## Step 7: Going Live Checklist

When ready for production:

- [ ] Get **LIVE** credentials from Moniepoint
- [ ] Update `.env` with live credentials
- [ ] Change environment in code from `'sandbox'` to `'live'`
- [ ] Test with small amounts first
- [ ] Set up webhook URL on Moniepoint dashboard
- [ ] Enable IP whitelisting (if required)
- [ ] Set up monitoring and logging
- [ ] Comply with Moniepoint's terms of service

---

## 📞 Moniepoint Support

If you encounter issues:

1. **Documentation**: https://developer.moniepoint.com/docs
2. **Support Email**: developer.support@moniepoint.com
3. **Business Support**: business@teamapt.com
4. **Phone**: Check their website for contact numbers

---

## 🔍 What to Look for in Moniepoint Confluence

When you're logged into their Confluence, check these sections:

1. **Getting Started** → API Overview
2. **Authentication** → How to generate tokens
3. **Virtual Accounts** → Account creation API
4. **Disbursements** → Transfer/withdrawal API
5. **Webhooks** → Real-time notifications
6. **Sample Code** → Python/Django examples
7. **Postman Collection** → Pre-built API tests

---

## 🚀 Your Current Integration Status

✅ **Completed**:
- Moniepoint API wrapper created (`moniepoint.py`)
- Payment processor implemented (`payment.py`)
- Webhook handler ready
- Settings configured for sandbox/live switching

⏳ **Next Steps**:
1. Get real Moniepoint credentials
2. Update `.env` file
3. Test virtual account creation
4. Test deposits and transfers
5. Configure webhooks on Moniepoint dashboard

---

**Need help?** Share your Moniepoint dashboard screenshots (without showing credentials) and I'll guide you through the specific steps!
