# Frontend Testing Guide

This guide covers testing the Chatbot L0027 frontend components in both development and production environments.

## Frontend Components

The frontend includes:

1. **Standalone Widget** (`widget.html`) - Full-page chatbot interface
2. **Embed Script** (`embed.js`) - JavaScript widget for integration
3. **React Component** (`react/ChatbotL0027.jsx`) - React integration
4. **Vue Component** (`vue/ChatbotL0027.vue`) - Vue.js integration
5. **Integration Guide** (`integration-guide.html`) - Demo examples

## Environment URLs

### Development

- **Base URL**: `http://localhost:8000`
- **API URL**: `http://localhost:8000/api/v1`
- **Widget URL**: `http://localhost:8000/widget`
- **Embed Script**: `http://localhost:8000/embed.js`

### Production

- **Base URL**: `https://chatbot.dfgp.fonctionpublique.gov.gn`
- **API URL**: `https://chatbot.dfgp.fonctionpublique.gov.gn/api/v1`
- **Widget URL**: `https://chatbot.dfgp.fonctionpublique.gov.gn/widget`
- **Embed Script**: `https://chatbot.dfgp.fonctionpublique.gov.gn/embed.js`

## Testing Methods

### 1. Standalone Widget Testing

Test the full-page widget interface.

#### Development

```bash
# Start development environment
./start-dev.sh

# Open in browser
open http://localhost:8000/widget
# or
curl http://localhost:8000/widget
```

#### Production

```bash
# Deploy production (if not already deployed)
./deploy-production.sh

# Open in browser
open https://chatbot.dfgp.fonctionpublique.gov.gn/widget
```

**Direct URLs:**
- Dev: `http://localhost:8000/widget`
- Prod: `https://chatbot.dfgp.fonctionpublique.gov.gn/widget`

### 2. Embed Script Testing

Test the JavaScript embed script that can be integrated into any website.

#### Quick Test Page

Create a simple HTML file to test the embed:

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Chatbot Embed</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 { color: #333; }
        p { line-height: 1.6; }
    </style>
</head>
<body>
    <h1>Test Page for Chatbot L0027</h1>
    <p>Scroll down to see the chatbot button appear in the bottom-right corner.</p>
    <p>Click the button to open the chatbot interface.</p>
    
    <!-- Development -->
    <script src="http://localhost:8000/embed.js" 
            data-api-url="http://localhost:8000/api/v1"
            data-position="bottom-right"
            data-theme="blue">
    </script>
    
    <!-- Production (comment out dev script above and uncomment this) -->
    <!--
    <script src="https://chatbot.dfgp.fonctionpublique.gov.gn/embed.js" 
            data-api-url="https://chatbot.dfgp.fonctionpublique.gov.gn/api/v1"
            data-position="bottom-right"
            data-theme="blue">
    </script>
    -->
</body>
</html>
```

Save as `test-embed-dev.html` or `test-embed-prod.html` and open in browser.

#### Testing in Existing Website

Add to any HTML page:

```html
<!-- Development -->
<script src="http://localhost:8000/embed.js" 
        data-api-url="http://localhost:8000/api/v1"
        data-position="bottom-right"
        data-theme="blue">
</script>

<!-- Production -->
<script src="https://chatbot.dfgp.fonctionpublique.gov.gn/embed.js" 
        data-api-url="https://chatbot.dfgp.fonctionpublique.gov.gn/api/v1"
        data-position="bottom-right"
        data-theme="blue">
</script>
```

**Configuration Options:**

```html
<script src="URL/embed.js"
        data-api-url="API_URL"           <!-- Required: API endpoint -->
        data-position="bottom-right"     <!-- Optional: bottom-right | bottom-left -->
        data-theme="blue"                <!-- Optional: blue | green | dark -->
        data-width="380px"               <!-- Optional: Widget width -->
        data-height="600px"              <!-- Optional: Widget height -->
        data-button-size="60px">         <!-- Optional: Button size -->
</script>
```

### 3. React Component Testing

#### Installation

```bash
npm install axios  # If not already installed
```

#### Usage in React App

```jsx
import React from 'react';
import ChatbotL0027 from './frontend/react/ChatbotL0027';

function App() {
  return (
    <div className="App">
      <h1>My App</h1>
      
      {/* Development */}
      <ChatbotL0027 
        apiUrl="http://localhost:8000/api/v1"
        theme="blue"
        position="bottom-right"
      />
      
      {/* Production */}
      {/* 
      <ChatbotL0027 
        apiUrl="https://chatbot.dfgp.fonctionpublique.gov.gn/api/v1"
        theme="blue"
        position="bottom-right"
      />
      */}
    </div>
  );
}

export default App;
```

#### Testing React Component

```bash
# In your React project
cd your-react-app

# Copy component
cp ../frontend/react/ChatbotL0027.jsx src/components/

# Import and use in your component
# Then start dev server
npm start

# Ensure backend is running on localhost:8000 (dev) or chatbot.dfgp.fonctionpublique.gov.gn (prod)
```

### 4. Vue Component Testing

#### Installation

```bash
npm install axios  # If not already installed
```

#### Usage in Vue App

```vue
<template>
  <div id="app">
    <h1>My App</h1>
    
    <!-- Development -->
    <ChatbotL0027 
      api-url="http://localhost:8000/api/v1"
      theme="blue"
      position="bottom-right"
    />
    
    <!-- Production -->
    <!-- 
    <ChatbotL0027 
      api-url="https://chatbot.dfgp.fonctionpublique.gov.gn/api/v1"
      theme="blue"
      position="bottom-right"
    />
    -->
  </div>
</template>

<script>
import ChatbotL0027 from './components/frontend/vue/ChatbotL0027.vue';

export default {
  name: 'App',
  components: {
    ChatbotL0027
  }
}
</script>
```

#### Testing Vue Component

```bash
# In your Vue project
cd your-vue-app

# Copy component
cp ../frontend/vue/ChatbotL0027.vue src/components/

# Import and use in your component
# Then start dev server
npm run serve

# Ensure backend is running on localhost:8000 (dev) or chatbot.dfgp.fonctionpublique.gov.gn (prod)
```

### 5. Integration Guide Testing

Test all integration methods using the demo page.

#### Development

```bash
# Open integration guide
open http://localhost:8000/static/integration-guide.html
# or
python -m http.server 8080 -d frontend
open http://localhost:8080/integration-guide.html
```

#### Production

```bash
# Deploy and access
open https://chatbot.dfgp.fonctionpublique.gov.gn/static/integration-guide.html
```

## Testing Checklist

### Basic Functionality

- [ ] Widget loads and displays correctly
- [ ] Chat button appears in correct position
- [ ] Chat interface opens when button is clicked
- [ ] Messages can be sent
- [ ] Responses are received correctly
- [ ] Loading states work properly
- [ ] Error messages display correctly

### Configuration Testing

- [ ] Different themes work (blue, green, dark)
- [ ] Position changes work (bottom-right, bottom-left)
- [ ] Custom width/height work
- [ ] API URL can be changed

### Cross-Browser Testing

Test in:
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

### Responsive Testing

- [ ] Desktop (1920x1080, 1366x768)
- [ ] Tablet (768x1024, 1024x768)
- [ ] Mobile (375x667, 414x896)

### Performance Testing

- [ ] Widget loads quickly (< 2 seconds)
- [ ] Messages send/receive promptly
- [ ] No memory leaks during extended use
- [ ] Smooth animations

### Security Testing

- [ ] HTTPS works in production
- [ ] CORS is configured correctly
- [ ] No sensitive data exposed in client
- [ ] API endpoints are secure

## Automated Testing

### Manual Test Script

Create a test script to verify API connectivity:

```javascript
// test-api.js
const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

async function testAPI() {
  try {
    // Test health endpoint
    const health = await fetch(`${API_URL.replace('/api/v1', '')}/health`);
    console.log('Health check:', await health.json());
    
    // Test API endpoint
    const response = await fetch(`${API_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: 'Test question',
        conversation_id: null
      })
    });
    
    const data = await response.json();
    console.log('API Response:', data);
    console.log('✅ API is working!');
  } catch (error) {
    console.error('❌ API Error:', error);
  }
}

testAPI();
```

Run with:
```bash
# Development
API_URL=http://localhost:8000/api/v1 node test-api.js

# Production
API_URL=https://chatbot.dfgp.fonctionpublique.gov.gn/api/v1 node test-api.js
```

## Troubleshooting

### CORS Issues

If you see CORS errors:

1. **Development**: Ensure CORS allows your origin
   - Check `app/main.py` CORS configuration
   - Ensure `DEBUG=true` allows all origins

2. **Production**: Verify CORS configuration
   - Check `app/core/config.py` CORS_ORIGINS
   - Ensure your domain is in the allowed list
   - Check Traefik CORS middleware

### Widget Not Loading

1. Check browser console for errors
2. Verify API URL is correct and accessible
3. Check network tab for failed requests
4. Ensure backend is running

### Messages Not Sending

1. Verify API endpoint is correct
2. Check network requests in browser dev tools
3. Verify backend is responding
4. Check API logs for errors

### Styling Issues

1. Clear browser cache
2. Check for CSS conflicts
3. Verify widget container positioning
4. Check z-index conflicts

## Quick Test Commands

### Development

```bash
# Start backend
./start-dev.sh

# Test widget
curl http://localhost:8000/widget

# Test embed script
curl http://localhost:8000/embed.js

# Test API
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Test"}'
```

### Production

```bash
# Test widget
curl https://chatbot.dfgp.fonctionpublique.gov.gn/widget

# Test embed script
curl https://chatbot.dfgp.fonctionpublique.gov.gn/embed.js

# Test API
curl -X POST https://chatbot.dfgp.fonctionpublique.gov.gn/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Test"}'
```

## Example Test Pages

See `frontend/test-embed-dev.html` and `frontend/test-embed-prod.html` for ready-to-use test pages.

## Support

For issues:
- Check browser console for errors
- Check backend logs: `docker compose logs chatbot`
- Check API documentation: `http://localhost:8000/docs` or `https://chatbot.dfgp.fonctionpublique.gov.gn/docs`

