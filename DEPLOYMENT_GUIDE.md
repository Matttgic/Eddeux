# 🚀 Secure Deployment Guide for Streamlit Cloud

## 🔒 SECURITY ISSUE RESOLVED

✅ **All hardcoded API keys have been removed from the codebase**
✅ **Environment variables properly configured**
✅ **API key validation added to the application**
✅ **Security status monitoring implemented**

---

## 📋 Pre-Deployment Checklist

### 1. 🔑 Secure Your API Key
- [ ] **IMMEDIATELY** regenerate your RapidAPI key (the old one was exposed)
- [ ] Go to [RapidAPI Dashboard](https://rapidapi.com/developer/dashboard)
- [ ] Navigate to your Pinnacle Odds subscription
- [ ] Click "Regenerate" to get a new key

### 2. 📂 Repository Preparation
- [ ] Ensure `.env` is in `.gitignore` (✅ Already done)
- [ ] Remove any cached files with sensitive data
- [ ] Verify no hardcoded keys remain in the code

---

## 🌐 Streamlit Cloud Deployment

### Step 1: Create Streamlit Cloud App
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set **Main file path:** `modernized_app.py`
4. Click "Deploy!"

### Step 2: Configure Secrets
1. In your Streamlit Cloud dashboard, click on your app
2. Go to **Settings** → **Secrets**
3. Add this configuration (replace with your actual API key):

```toml
[secrets]
PINNACLE_API_KEY = "your_new_regenerated_api_key_here"
PINNACLE_HOST = "pinnacle-odds.p.rapidapi.com"
CACHE_DURATION = "5"
REQUEST_TIMEOUT = "30"
BANKROLL = "1000.0"
KELLY_FRACTION = "0.25"
MAX_BET_PERCENTAGE = "0.05"
LOG_LEVEL = "INFO"
DATA_DIR = "Données"
```

### Step 3: Verify Deployment
- [ ] Check that the security status shows "✅ API Key Configured"
- [ ] Test the "Refresh Analysis" function
- [ ] Verify live data is being fetched

---

## 💻 Local Development Setup

### Option 1: Using .env file
```bash
# Copy the template
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your preferred editor

# Add this line with your actual key:
PINNACLE_API_KEY=your_actual_api_key_here
```

### Option 2: Using environment variables
```bash
export PINNACLE_API_KEY="your_actual_api_key_here"
streamlit run modernized_app.py
```

---

## 🛡️ Security Features Implemented

### 1. **API Key Validation**
- Application checks for valid API key on startup
- Shows clear error messages if key is missing or invalid
- Prevents execution with insecure configurations

### 2. **Environment Security**
- All sensitive data moved to environment variables
- No default API keys in the codebase
- Secure fallback behaviors

### 3. **Security Monitoring**  
- Real-time security status in sidebar
- Alerts for configuration issues
- Secure handling of credentials

### 4. **Safe Defaults**
- Empty API key by default (forces conscious configuration)
- Graceful degradation when services are unavailable
- Comprehensive error handling

---

## 🧪 Testing Your Deployment

### 1. **Security Test**
```bash
# Verify no API keys in code
grep -r "e1e76b8e3emsh" . 
# Should return no results

# Check environment setup
python -c "import os; print('API_KEY exists:', bool(os.getenv('PINNACLE_API_KEY')))"
```

### 2. **Functionality Test**
- [ ] App loads without errors
- [ ] Security status shows green checkmarks
- [ ] Analysis completes successfully
- [ ] Live data is fetched from API

---

## ⚠️ Important Security Notes

1. **Never commit API keys to Git**
   - The `.gitignore` file protects you
   - Always use environment variables or secrets management

2. **Regenerate compromised keys immediately**
   - Your original key was exposed in the public repository
   - Get a new one from RapidAPI before deploying

3. **Monitor your API usage**
   - Check RapidAPI dashboard for unusual activity
   - Set up usage alerts if available

4. **Use Streamlit Secrets for cloud deployment**
   - More secure than environment variables in cloud environments
   - Encrypted and access-controlled

---

## 🆘 Troubleshooting

### "API Key Missing" Error
- **Streamlit Cloud:** Check that secrets are properly configured
- **Local:** Verify `.env` file exists and contains your API key

### "Invalid API Key" Error  
- Ensure you've regenerated your API key after the exposure
- Check for extra spaces or characters in the key

### Services Not Starting
- This is expected behavior when no API key is configured
- Add your key and restart the application

---

## ✅ Final Checklist

- [ ] Old API key regenerated  
- [ ] New API key added to Streamlit secrets or local `.env`
- [ ] Application loads without security warnings
- [ ] Live data analysis working
- [ ] Repository is secure (no hardcoded keys)
- [ ] `.gitignore` protects sensitive files

**🎉 Your Tennis Value Betting System is now securely deployed!**