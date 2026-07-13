import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext({})

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simular carregamento inicial do localStorage
    const savedUser = localStorage.getItem('@aacc_mock_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
    setLoading(false)
  }, [])

  const login = (role) => {
    const mockUser = {
      id: role === 'aluno' ? 1 : 2,
      name: role === 'aluno' ? 'João Silva' : 'Prof. Carlos Admin',
      email: role === 'aluno' ? 'joao.silva@unitins.br' : 'carlos.coord@unitins.br',
      role: role,
    }
    setUser(mockUser)
    localStorage.setItem('@aacc_mock_user', JSON.stringify(mockUser))
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('@aacc_mock_user')
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
