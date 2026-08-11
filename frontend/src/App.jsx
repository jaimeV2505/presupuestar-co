import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Editor from './pages/Editor'
import VistaPublica from './pages/VistaPublica'
import Perfil from './pages/Perfil'

function Privada({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" toastOptions={{ style: { fontSize: '14px' } }} />
      <Routes>
        <Route path="/login" element={<Login modo="login" />} />
        <Route path="/registro" element={<Login modo="registro" />} />
        <Route path="/p/:token" element={<VistaPublica />} />
        <Route path="/" element={<Privada><Dashboard /></Privada>} />
        <Route path="/editor/:id" element={<Privada><Editor /></Privada>} />
        <Route path="/perfil" element={<Privada><Perfil /></Privada>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
