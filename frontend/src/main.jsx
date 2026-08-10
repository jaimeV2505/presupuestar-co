import React from 'react'
import ReactDOM from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <Toaster position="top-right" toastOptions={{
      duration: 4000,
      style: { fontFamily:'Inter,sans-serif', fontSize:'13px', borderRadius:'10px', border:'1px solid #E2E8F0' },
      success: { iconTheme:{primary:'#10B981',secondary:'#fff'} },
      error:   { iconTheme:{primary:'#EF4444',secondary:'#fff'} },
    }} />
  </React.StrictMode>
)
