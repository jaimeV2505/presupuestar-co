import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Editor from './pages/Editor'
import VistaPublica from './pages/VistaPublica'
import Perfil from './pages/Perfil'
import Landing from './pages/Landing'
import Pro from './pages/Pro'
import Admin from './pages/Admin'

function Privada({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

function Inicio() {
  const token = localStorage.getItem('token')
  return token ? <Dashboard /> : <Landing />
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" toastOptions={{ style: { fontSize: '14px' } }} />
      <Routes>
        <Route path="/login" element={<Login modo="login" />} />
        <Route path="/registro" element={<Login modo="registro" />} />
        <Route path="/p/:token" element={<VistaPublica />} />
        <Route path="/" element={<Inicio />} />
        <Route path="/editor/:id" element={<Privada><Editor /></Privada>} />
        <Route path="/perfil" element={<Privada><Perfil /></Privada>} />
        <Route path="/pro" element={<Privada><Pro /></Privada>} />
        <Route path="/admin" element={<Privada><Admin /></Privada>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
