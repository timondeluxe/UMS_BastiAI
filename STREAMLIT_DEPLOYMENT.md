# Streamlit Deployment Guide

## 🚀 Quick Start

### 1. Local Testing
```bash
# Install dependencies
pip install -r requirements_streamlit.txt

# Set up environment variables
cp env_streamlit_template.txt .env
# Edit .env with your actual API keys

# Run locally
streamlit run streamlit_app.py
```

### 2. Deploy to Streamlit Community Cloud

#### Step 1: Prepare Repository
1. Push your code to GitHub
2. Ensure `streamlit_app.py` is in the root directory
3. Include `requirements_streamlit.txt`

#### Step 2: Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select your repository
4. Set main file path: `streamlit_app.py`
5. Add environment variables in the dashboard

#### Step 3: Environment Variables
Add these in Streamlit Cloud dashboard:
```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
SUPABASE_SECRET_KEY=your_supabase_secret_key
```

## 🔧 Configuration

### Debug Mode
- **Sidebar Toggle**: Use checkbox in sidebar
- **URL Parameter**: Add `?debug=true` to URL
- **Console Logging**: Check browser console for detailed logs

### Features
- ✅ Chat interface with question/answer
- ✅ Confidence scoring for responses
- ✅ Debug mode with sources and timing
- ✅ Chat history management
- ✅ Responsive design
- ✅ Error handling

## 📊 Cost Estimation

### Hosting
- **Streamlit Community Cloud**: FREE
- **Custom Domain**: Optional ($5-10/month)

### API Costs (OpenAI)
- **Per Question**: ~$0.0001-0.0002
- **100 questions/month**: ~$0.01-0.02
- **1,000 questions/month**: ~$0.10-0.20
- **10,000 questions/month**: ~$1-2

### Database (Supabase)
- **Free Tier**: 500MB, 2GB bandwidth
- **Pro Plan**: $25/month (if needed)

## 🛠️ Troubleshooting

### Common Issues
1. **Agent initialization fails**: Check API keys
2. **No responses**: Verify Supabase connection
3. **Slow responses**: Check OpenAI API limits
4. **Debug mode not working**: Clear browser cache

### Support
- Check logs in Streamlit Cloud dashboard
- Use debug mode for detailed information
- Verify environment variables are set correctly

## 🔒 Security Notes

- Never commit API keys to repository
- Use Streamlit Cloud's environment variables
- Consider rate limiting for production use
- Monitor API usage and costs

## 📈 Scaling

### For Higher Usage
1. **Upgrade Supabase**: Pro plan for more data
2. **Custom Hosting**: AWS/GCP for better performance
3. **Caching**: Implement response caching
4. **Rate Limiting**: Add user limits

### Performance Optimization
- Use connection pooling
- Implement response caching
- Optimize embedding queries
- Monitor API response times
