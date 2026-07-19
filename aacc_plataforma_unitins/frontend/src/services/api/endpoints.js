import api from './client'

export const certificadosService = {
  listar:  (params) => api.get('/academico/certificados/', { params }),
  obter:   (id)     => api.get(`/academico/certificados/${id}/`),
  criar:   (data)   => api.post('/academico/certificados/', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  atualizar: (id, data) => api.patch(`/academico/certificados/${id}/`, data),
  remover:   (id)       => api.delete(`/academico/certificados/${id}/`),
  avaliar:   (id, data) => api.patch(`/academico/certificados/${id}/avaliar/`, data),
}

export const alunoService = {
  listarAlunos:    ()          => api.get('/academico/alunos/'),
  obterMeuExtrato: ()          => api.get('/academico/alunos/meu-extrato/'),
  obterExtrato:    (perfilId)  => api.get(`/academico/alunos/${perfilId}/extrato/`),
}

export const categoriasService = {
  listar: (params) => api.get('/academico/categorias/', { params }),
  obter:  (id)     => api.get(`/academico/categorias/${id}/`),
}

export const authService = {
  login:   (credentials) => api.post('/accounts/token/', credentials),
  refresh: (refresh)     => api.post('/accounts/token/refresh/', { refresh }),
  me:      ()            => api.get('/accounts/me/'),
}
