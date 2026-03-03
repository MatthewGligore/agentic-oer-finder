# Frontend - React + Vite

Modern React application built with Vite for the Agentic OER Finder.

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production (outputs to `dist/`)
- `npm run preview` - Preview production build locally

## Project Structure

```
src/
├── components/
│   ├── SearchForm.jsx       # Course search form
│   ├── SearchForm.css
│   ├── Results.jsx          # Results display
│   └── Results.css
├── services/
│   └── oerAPI.js           # API calls to backend
├── App.jsx                  # Main app component
├── App.css
├── index.css
└── main.jsx                 # React entry point
```

## Technology Stack

- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **Axios**: HTTP client for API calls
- **CSS 3**: Styling with animations and responsive design

## Configuration

### API Proxy

The dev server proxies `/api` requests to `http://localhost:5000` (Flask backend).
See `vite.config.js` for proxy configuration.

### Environment

Development runs on `http://localhost:3000`
Production builds to the `dist/` directory.

## Building for Production

```bash
npm run build
```

The build output in `dist/` contains:
- Optimized JavaScript bundles
- CSS modules
- Static assets

Deploy the `dist/` folder to your web server or CDN.

## Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Search**: Search for OER by course code
- **Resource Cards**: Clean display of resources with quality scores
- **Integration Tips**: Suggestions for using resources in courses
- **License Info**: Shows open license information
- **Error Handling**: User-friendly error messages

## Styling

- Modular CSS files per component
- Responsive grid layout
- Smooth animations and transitions
- Accessible color scheme and typography

## API Integration

The `services/oerAPI.js` module handles all backend communication:

```javascript
// Search for resources
const results = await oerAPI.search('ENGL 1101', 'Fall 2025')

// Get statistics
const stats = await oerAPI.getStats()
```

## Development Tips

- Use React DevTools browser extension for debugging
- Check the browser console for API error details
- Vite supports fast HMR (Hot Module Reload) for rapid development
- Component CSS is colocated with components for better organization

## Performance

- Code splitting for faster load times
- Lazy loading of components
- CSS optimization in production build
- Minimal bundle size with selective dependencies
