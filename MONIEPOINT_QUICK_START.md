# 🎯 MONIEPOINT QUICK REFERENCE

## 📍 WHERE TO UPDATE CREDENTIALS

### File Location:
```
C:\Users\awaje\Documents\jefferson\documents\GAX\.env
```

### Lines to Update (Lines 18-22):
```env
MONIEPOINT_SANDBOX_BASE_URL=https://sandbox.moniepoint.com/api/v1
MONIEPOINT_SANDBOX_API_KEY=YOUR_KEY_HERE
MONIEPOINT_SANDBOX_SECRET_KEY=YOUR_SECRET_HERE
MONIEPOINT_SANDBOX_CONTRACT_CODE=YOUR_CONTRACT_HERE
MONIEPOINT_SANDBOX_CLIENT_ID=YOUR_CLIENT_ID_HERE
```

---

## 🔑 WHAT YOU NEED FROM MONIEPOINT DASHBOARD

When you login to https://developer.moniepoint.com/, copy these 5 values:

| Field | Example | Where to Paste |
|-------|---------|----------------|
| Base URL | `https://sandbox.moniepoint.com/api/v1` | Line 18 in .env |
| API Key | `MK_TEST_ABC123XYZ` | Line 19 in .env |
| Secret Key | `sk_test_SECRET123` | Line 20 in .env |
| Contract Code | `1234567890` | Line 21 in .env |
| Client ID | `CLIENT_ABC123` | Line 22 in .env |

---

## 📋 STEP-BY-STEP CHECKLIST

### 1️⃣ Get Moniepoint Access
- [ ] Go to https://developer.moniepoint.com/
- [ ] Create account or login
- [ ] Verify your business (if required)

### 2️⃣ Create Application
- [ ] Click "My Apps" or "Applications"
- [ ] Create new app: "GAX Banking"
- [ ] Set callback: `http://127.0.0.1:8000/api/webhooks/moniepoint/`

### 3️⃣ Copy Credentials
- [ ] Copy API Key
- [ ] Copy Secret Key  
- [ ] Copy Contract Code
- [ ] Copy Client ID
- [ ] Copy Base URL

### 4️⃣ Update .env File
- [ ] Open: `C:\Users\awaje\Documents\jefferson\documents\GAX\.env`
- [ ] Paste API Key on line 19
- [ ] Paste Secret Key on line 20
- [ ] Paste Contract Code on line 21
- [ ] Paste Client ID on line 22
- [ ] Save file

### 5️⃣ Test Integration
- [ ] Restart Django server
- [ ] Register a test user
- [ ] Try deposit/transfer
- [ ] Check if virtual account created

---

## 🔄 RESTART SERVER AFTER UPDATING .ENV

```powershell
# Stop current server (Ctrl+C in terminal)
# Then restart:
cd C:\Users\awaje\Documents\jefferson\documents\GAX\gax\banking
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

---

## 🧪 TEST YOUR SETUP

### Test 1: Check if credentials are loaded
```python
# In Django shell
python manage.py shell

from django.conf import settings
print(settings.MONIEPOINT_SANDBOX_API_KEY)
# Should print your actual key, not "test-api-key"
```

### Test 2: Create a user and check virtual account
```bash
# Register user via API
# Then check if virtual account was created in database
```

---

## ⚠️ COMMON ISSUES

### Issue: "Authentication Failed"
**Solution**: Double-check your API Key and Secret Key

### Issue: "Invalid Contract Code"
**Solution**: Verify contract code matches your Moniepoint dashboard

### Issue: "Webhook not receiving"
**Solution**: 
1. Update webhook URL in Moniepoint dashboard
2. Use ngrok for local testing: `ngrok http 8000`

---

## 📞 NEED HELP?

1. Read full guide: `MONIEPOINT_SETUP_GUIDE.md`
2. Check Moniepoint docs: https://developer.moniepoint.com/docs
3. Email support: developer.support@moniepoint.com

---

## 🎯 CURRENT STATUS

✅ Code is ready - just waiting for real credentials!

**What's already integrated:**
- ✅ Moniepoint API wrapper (`moniepoint.py`)
- ✅ Payment processor (`payment.py`)  
- ✅ Webhook handler (`api_views.py`)
- ✅ Environment configuration (`.env`)
- ✅ Settings configured (`settings.py`)

**What you need to do:**
- ⏳ Get credentials from Moniepoint
- ⏳ Update `.env` file
- ⏳ Test the integration

---

**Once you get your Moniepoint credentials, just paste them in the .env file and you're good to go! 🚀**
