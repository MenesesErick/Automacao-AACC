import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { jwtDecode } from 'jwt-decode'
import api, { setTokens, clearTokens } from '@/services/api/client'

const AuthContext = createContext({})

/**
 * Extrai os dados relevantes do payload do JWT e mapeia para o estado do utilizador.
 * Funciona com os claims customizados definidos em accounts/serializers.py.
 */
function extrairPerfilDoToken(accessToken) {
  try {
    const payload = jwtDecode(accessToken)
    return {
      id:              payload.user_id,
      nome:            payload.nome   || 'Utilizador',
      email:           payload.email  || '',
      // O role é derivado dos claims de perfil injetados no backend
      role:            payload.is_superuser ? 'admin' : (payload.is_coordenador ? 'coordenador' : 'aluno'),
      is_aluno:        payload.is_aluno        ?? false,
      is_coordenador:  payload.is_coordenador  ?? false,
      is_superuser:    payload.is_superuser    ?? false,
    }
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Hidrata o estado a partir do token guardado no localStorage
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      const perfil = extrairPerfilDoToken(token)
      if (perfil) {
        setUser(perfil)
      } else {
        // Token corrompido ou expirado — limpa
        clearTokens()
      }
    }
    setLoading(false)
  }, [])

  /**
   * Autentica o utilizador via POST /api/accounts/token/.
   * @param {string} email    - Email institucional (@unitins.br)
   * @param {string} password - Senha
   * @throws {Error} friendlyMessage vindo da API (ex: domínio inválido)
   */
  const login = useCallback(async (email, password) => {
    // O simplejwt usa o campo "username" por padrão
    const { data } = await api.post('/accounts/token/', {
      username: email,
      password,
    })

    setTokens({ access: data.access, refresh: data.refresh })

    const perfil = extrairPerfilDoToken(data.access)
    setUser(perfil)

    return perfil
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
