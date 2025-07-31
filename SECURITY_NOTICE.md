# 🔒 SECURITY NOTICE - API Key Management

## ⚠️ IMPORTANT: Your API key was exposed in the code!

The API key `6` was hardcoded in the source files. 

**IMMEDIATE ACTIONS REQUIRED:**

### 1. 🔑 Regenerate Your API Key
- Go to your RapidAPI dashboard
- Navigate to your Pinnacle Odds subscription
- **Regenerate your API key immediately**
- The exposed key should be considered compromised

### 2. 🚫 Add .env to .gitignore
Never commit sensitive environment files to version control.

### 3. 📝 For Streamlit Cloud Deployment
Add your secrets in Streamlit Cloud's secrets management:

**In Streamlit Cloud Dashboard:**
1. Go to your app settings
2. Click "Secrets" 
3. Add this content:

```toml
[secrets]
PINNACLE_API_KEY = "your_new_api_key_here"
PINNACLE_HOST = "pinnacle-odds.p.rapidapi.com"
CACHE_DURATION = "5"
REQUEST_TIMEOUT = "30"
BANKROLL = "1000.0"
KELLY_FRACTION = "0.25"
MAX_BET_PERCENTAGE = "0.05"
LOG_LEVEL = "INFO"
DATA_DIR = "Données"
```

### 4. 🔒 Local Development
Copy `.env.example` to `.env` and add your real API key:

```bash
cp .env.example .env
# Edit .env with your actual API key
```

### 5. ✅ Security Features Added
- ✅ Removed all hardcoded API keys
- ✅ Added environment variable validation
- ✅ Created secure configuration management
- ✅ Added API key validation in the app
- ✅ Enhanced error handling for missing keys

## 🛡️ Best Practices Applied:
- Environment variables for all sensitive data
- No default API keys in production code
- Graceful degradation when keys are missing
- Security warnings in the UI
- Comprehensive logging without exposing secrets
