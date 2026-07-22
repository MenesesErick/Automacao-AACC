# AACC Platform — Plataforma de Gestão de Atividades Acadêmico-Científico-Culturais

> **Universidade Estadual do Tocantins — UNITINS**  
> Curso de Sistemas de Informação  
> Versão atual: `0.1.0` · Status: **Em desenvolvimento ativo**

---

## Índice

1. [Contexto e Motivação](#1-contexto-e-motivação)
2. [Regras de Negócio (RNs)](#2-regras-de-negócio-rns)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Stack Tecnológica](#4-stack-tecnológica)
5. [Estrutura de Diretórios](#5-estrutura-de-diretórios)
6. [Modelos de Dados (Backend)](#6-modelos-de-dados-backend)
7. [API REST — Endpoints](#7-api-rest--endpoints)
8. [Perfis de Utilizador e Permissões](#8-perfis-de-utilizador-e-permissões)
9. [Frontend — Componentes e Páginas](#9-frontend--componentes-e-páginas)
10. [Fluxos Principais (User Journeys)](#10-fluxos-principais-user-journeys)
11. [Motor de Regras (Rule Engine)](#11-motor-de-regras-rule-engine)
12. [Infraestrutura de Testes — Fábrica Sintética](#12-infraestrutura-de-testes--fábrica-sintética)
13. [Guia de Configuração e Desenvolvimento](#13-guia-de-configuração-e-desenvolvimento)
14. [Variáveis de Ambiente](#14-variáveis-de-ambiente)
15. [Comandos de Gestão Django](#15-comandos-de-gestão-django)
16. [Decisões de Design e Filosofia](#16-decisões-de-design-e-filosofia)
17. [Roadmap — Funcionalidades Pendentes](#17-roadmap--funcionalidades-pendentes)

---

## 1. Contexto e Motivação

As **Atividades Acadêmico-Científico-Culturais (AACC)** são requisito obrigatório para a conclusão do curso de Sistemas de Informação da UNITINS, regulamentadas pela **Resolução CONSUNI nº 057/2025**. Os alunos devem acumular um número mínimo de horas em atividades complementares distribuídas por três eixos curriculares: **Ensino**, **Pesquisa** e **Extensão**.

**O problema atual:**
- O processo é inteiramente manual: os alunos entregam documentos em papel ou PDFs por e-mail.
- A coordenação valida cada documento individualmente, sem sistematização.
- Não há rastreabilidade do histórico, nem alertas automáticos de eligibilidade para formatura.
- O processo é propenso a erros, fraudes por documentos forjados e inconsistências nos cálculos de horas.

**A solução — AACC Platform:**

Uma plataforma web full-stack que digitaliza e automatiza todo o ciclo de vida dos certificados AACC:

```
Submissão (Aluno) → OCR Engine (Regex) → IA Sugere Horas → Motor de Regras → Revisão Manual (Human-in-the-Loop) → Dashboard
```

A plataforma implementa um **pipeline de auditoria rastreável**: cada decisão sobre um certificado é gravada com justificativa, artigo da resolução aplicado, horas computadas e horas descartadas.

---

## 2. Regras de Negócio (RNs)

As regras derivam diretamente da Resolução CONSUNI nº 057/2025 e são implementadas no `rule_engine/`.

| ID | Nome | Descrição | Status |
|----|------|-----------|--------|
| **RN01** | Extração OCR | Extrair texto e horas via Regex + PyMuPDF em paradigma Human-in-the-Loop | Implementado |
| **RN02** | Diversidade de Eixos | O aluno deve ter horas em pelo menos 2 dos 3 eixos (Ensino, Pesquisa, Extensão) para ser apto | Implementado |
| **RN03** | Teto por Categoria | Horas aprovadas em cada categoria são limitadas ao `limite_maximo_horas` | Implementado |
| **RN04** | Detecção de Duplicatas | Documentos com hash idêntico devem ser rejeitados automaticamente | Planejado |
| **RN05** | Revisão Manual (Human-in-the-Loop) | Coordenadores podem deferir/indeferir certificados | Implementado |
| **RN06** | Requerimento Final (Anexo I) | Geração automática do PDF "Anexo I" para alunos aptos | Planejado |

### Fórmula de Aptidão para Formatura (RN02)

```
apto_formatura = (total_horas_aprovadas >= meta_horas) AND (eixos_com_horas >= 2)
```

---

## 3. Arquitetura do Sistema

```
+-------------------------------------------------------------+
|                       AACC Platform                         |
|                                                             |
|  +------------------+          +-------------------------+  |
|  |    Frontend      |  HTTP/S  |        Backend          |  |
|  |  React + Vite   |<-------->|  Django REST Framework  |  |
|  |  Tailwind CSS   |   JWT    |  PostgreSQL / Redis      |  |
|  +------------------+          +-------------------------+  |
|        :5173                             :8000              |
|                                                             |
|  Módulos Backend:                                           |
|  +-------------+  +------------+  +----------------+       |
|  |  accounts   |  |  academico |  |  rule_engine   |       |
|  | (Auth/JWT)  |  | (Core API) |  |  (RN01-RN04)   |       |
|  +-------------+  +------------+  +----------------+       |
+-------------------------------------------------------------+
```

### Fluxo de dados de um certificado

```
Aluno → [POST /certificados/] → Salva PDF em media/
    → ocr_service (PyMuPDF + Regex) extrai texto e sugere horas
    → ValidadorCertificado.processar_certificado()
        → Aplica RN03 (teto por categoria)
        → Grava RuleValidationLog (Auditoria)
        → Define status: pendente_ocr | revisao_manual | aprovado | rejeitado
    → Coordenador revisa via [PATCH /certificados/{id}/avaliar/]
    → Status final refletido no dashboard do aluno
```

---

## 4. Stack Tecnológica

### Backend

| Tecnologia | Versão | Função |
|---|---|---|
| Python | 3.14 | Linguagem principal |
| Django | 4.2.30 | Framework web principal |
| Django REST Framework | 3.17.1 | Construção da API REST |
| djangorestframework-simplejwt | 5.5.1 | Autenticação JWT stateless |
| django-cors-headers | 4.9.0 | Política CORS para o frontend |
| psycopg2-binary | 2.9.12 | Driver PostgreSQL |
| python-decouple | 3.8 | Gestão de variáveis de ambiente (.env) |
| ReportLab | 5.0.0 | Geração de PDFs (sintéticos e Anexo I) |
| PyMuPDF (fitz) | 1.28.0 | Extração de texto para o Pipeline de OCR |
| Pillow | 12.3.0 | Processamento de imagens (fundos de PDF) |
| Faker | 40.31.0 | Dados fictícios para a fábrica sintética |
| Celery | 5.6.3 | Filas de tarefas assíncronas |
| Redis | 8.0.1 | Broker para Celery |

### Frontend

| Tecnologia | Versão | Função |
|---|---|---|
| React | 18.3.1 | Biblioteca de UI |
| Vite | 5.3.1 | Build tool e dev server |
| Tailwind CSS | 3.4.4 | Framework de estilos utilitários |
| React Router DOM | 6.24.0 | Roteamento SPA |
| Axios | 1.7.2 | Cliente HTTP (integração com API) |
| Recharts | 3.9.2 | Gráficos (dashboard de extrato) |
| Lucide React | 0.395.0 | Biblioteca de ícones |
| jwt-decode | 4.0.0 | Decodificação de tokens JWT no cliente |
| clsx + tailwind-merge | — | Utilitários de classnames condicionais |

---

## 5. Estrutura de Diretórios

```
Automacao-AACC/
├── README.md
├── Contexto.md                        ← SSOT das regras de negócio
│
└── aacc_plataforma_unitins/
    ├── backend/
    │   ├── manage.py
    │   ├── requirements.txt
    │   ├── .env                       ← (não versionado)
    │   ├── aacc_core/                 ← Configurações globais Django
    │   │   ├── settings.py
    │   │   ├── urls.py
    │   │   ├── wsgi.py
    │   │   └── asgi.py
    │   ├── accounts/                  ← App de Autenticação
    │   │   ├── models.py              ← Usuario (custom AbstractUser)
    │   │   ├── serializers.py
    │   │   ├── views.py
    │   │   └── urls.py
    │   ├── academico/                 ← App Core do Domínio
    │   │   ├── models.py
    │   │   ├── serializers.py
    │   │   ├── views.py
    │   │   ├── urls.py
    │   │   └── management/commands/
    │   │       ├── seed_database.py   ← Seed de dados para UI/UX
    │   │       └── gerar_dataset.py   ← Fábrica de PDFs sintéticos
    │   ├── rule_engine/               ← Motor de Regras (RN01-RN04)
    │   │   ├── validator.py
    │   │   └── consuni_057.py
    │   ├── ocr_engine/               ← Pipeline OCR (em construção)
    │   └── media/
    │       ├── uploads_alunos/       ← PDFs de certificados
    │       ├── requerimentos_gerados/
    │       └── templates_base/       ← Fundos PNG para fábrica sintética
    │
    └── frontend/
        ├── package.json
        ├── vite.config.js
        ├── tailwind.config.js
        └── src/
            ├── main.jsx
            ├── App.jsx
            ├── components/
            │   ├── atoms/             ← Button, Input, Badge, Avatar
            │   ├── organisms/         ← CertificadoDrawer, AlunoRaioXDrawer,
            │   │                          ExtratoCharts, DataTable, StatsCard
            │   └── layout/            ← AppLayout, Sidebar, Header
            ├── pages/
            │   ├── auth/Login.jsx
            │   ├── aluno/             ← DashboardAluno, HistoricoAluno, EnviarCertificado
            │   └── coordenador/       ← DashboardCoordenador, FilaRevisao, GestaoAlunos
            ├── contexts/AuthContext.jsx
            ├── routes/index.jsx
            ├── services/api/
            │   ├── client.js          ← Axios com interceptor JWT
            │   └── endpoints.js       ← Funções de chamada à API
            ├── styles/global.css
            └── utils/cn.js
```

---

## 6. Modelos de Dados (Backend)

### `accounts.Usuario` (Custom User)

Extende `AbstractUser` do Django.

| Campo | Tipo | Descrição |
|---|---|---|
| `email` | EmailField (único) | Login via e-mail `@unitins.br` |
| `is_aluno` | BooleanField | Perfil de aluno ativo |
| `is_coordenador` | BooleanField | Perfil de coordenador ativo |

### `academico.CategoriaAACC`

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | CharField | Ex: "Monitoria e Tutoria" |
| `eixo` | CharField (choices) | `Ensino` / `Pesquisa` / `Extensao` |
| `limite_maximo_horas` | IntegerField | Teto de horas computáveis (RN03) |

### `academico.Certificado` (modelo central)

| Campo | Tipo | Descrição |
|---|---|---|
| `aluno` | FK → AlunoPerfil | Proprietário |
| `categoria` | FK → CategoriaAACC | Tipo de atividade |
| `arquivo_pdf` | FileField | PDF submetido |
| `horas_declaradas` | DecimalField | (Deprecado/Anulável) Horas preenchidas pelo aluno |
| `texto_extraido_ocr` | TextField | Texto bruto extraído pelo OCR |
| `horas_sugeridas_ia` | IntegerField | Horas encontradas pelo OCR/Regex |
| `confianca_ia` | IntegerField | Confiança do OCR em % |
| `horas_computadas_final` | IntegerField | Horas efetivamente aprovadas pelo coordenador |
| `horas_descartadas` | IntegerField | Horas cortadas pelo RN03 ou pela revisão |
| `status` | CharField (choices) | Ver ciclo de vida abaixo |
| `motivo_status` | CharField | Justificativa da decisão |
| `data_envio` | DateTimeField | Auto-preenchido |
| `data_atualizacao` | DateTimeField | Auto-atualizado |

**Ciclo de vida do `status`:**

```
pendente_ocr ──→ revisao_manual (baixa confiança OCR)
             ──→ aprovado       (alta confiança + RN03 OK)
             ──→ rejeitado      (duplicata / RN03 zera horas)

revisao_manual ──→ [Coordenador] ──→ aprovado | rejeitado
aprovado       ──→ requerimento_gerado (RN06)
```

### `academico.RuleValidationLog` (Auditoria Imutável)

| Campo | Tipo | Descrição |
|---|---|---|
| `certificado` | FK → Certificado | Certificado avaliado |
| `usuario_responsavel` | FK → Usuario | Coordenador (se manual) |
| `regra_aplicada` | CharField | Ex: "RN03 - Teto por Categoria" |
| `artigo_resolucao` | CharField | "Resolução CONSUNI nº 057/2025" |
| `justificativa` | TextField | Descrição da decisão |
| `horas_enviadas` | IntegerField | Horas declaradas |
| `horas_computadas` | IntegerField | Horas aprovadas |
| `horas_descartadas` | IntegerField | Horas rejeitadas |

---

## 7. API REST — Endpoints

**Base URL:** `http://127.0.0.1:8000/api/`

Todos os endpoints requerem `Authorization: Bearer <token>`.

### Autenticação

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/accounts/token/` | Login — retorna access + refresh |
| `POST` | `/accounts/token/refresh/` | Renovar token |
| `GET` | `/accounts/me/` | Perfil do utilizador logado |

### Certificados

| Método | Endpoint | Permissão | Descrição |
|---|---|---|---|
| `GET` | `/academico/certificados/` | Aluno / Coord. | Lista (filtrada por papel) |
| `POST` | `/academico/certificados/` | Aluno | Submeter novo certificado |
| `PATCH` | `/academico/certificados/{id}/avaliar/` | Coord. only | Deferir / Indeferir (RN05) |

**Payload de `avaliar`:**
```json
{
  "status": "aprovado",
  "horas_computadas_final": 20,
  "motivo_status": "Documento verificado e válido."
}
```

### Extrato (RN02)

| Método | Endpoint | Permissão | Descrição |
|---|---|---|---|
| `GET` | `/academico/alunos/meu-extrato/` | Aluno | Extrato do próprio aluno |
| `GET` | `/academico/alunos/{id}/extrato/` | Coord. | Extrato de aluno específico |
| `GET` | `/academico/alunos/` | Coord. | Lista todos os alunos |

**Resposta de `/meu-extrato/`:**
```json
{
  "aluno": "João Silva",
  "matricula": "2023001SI",
  "total_horas": 85,
  "meta": 200,
  "percentual": 42.5,
  "apto_formatura": false,
  "eixos_contemplados": 2,
  "eixos": {
    "Ensino":   { "horas": 40 },
    "Pesquisa": { "horas": 30 },
    "Extensao": { "horas": 15 }
  }
}
```

---

## 8. Perfis de Utilizador e Permissões

| Perfil | Acesso | Páginas disponíveis |
|---|---|---|
| **Aluno** | Apenas os seus próprios certificados | Dashboard, Enviar, Histórico |
| **Coordenador** | Visibilidade total | Dashboard Coord., Fila de Revisão, Gestão de Alunos |
| **Admin Django** | Painel `/admin/` completo | Gestão de dados brutos |

---

## 9. Frontend — Componentes e Páginas

### Design System — Tokens CSS

```css
--color-primary:      hsl(220, 90%, 56%);
--color-bg-surface:   hsl(220, 20%, 10%);
--color-text-primary: hsl(220, 15%, 95%);
--color-success:      hsl(142, 70%, 45%);
--color-danger:       hsl(0, 70%, 55%);
--color-warning:      hsl(38, 90%, 50%);
```

### Componentes-chave

**`CertificadoDrawer.jsx`** — Painel lateral de detalhes de certificado:
- Badge de status, metadados, iframe com PDF, formulário de decisão para coordenadores.

**`ExtratoCharts.jsx`** — Gráficos partilhados da RN02 (usados em 2 views):
- `BannerFormatura` — alerta de aptidão
- `GraficoProgresso` — barra radial de progresso total
- `GraficoEixos` — barras por eixo (Ensino / Pesquisa / Extensão)

**`AlunoRaioXDrawer.jsx`** — Drawer exclusivo do coordenador com extrato completo do aluno.

### Páginas

| Página | Rota | Perfil |
|---|---|---|
| Login | `/login` | Público |
| Dashboard Aluno | `/aluno/dashboard` | Aluno |
| Enviar Certificado | `/aluno/enviar` | Aluno |
| Meu Histórico | `/aluno/historico` | Aluno |
| Dashboard Coordenador | `/coordenador/dashboard` | Coordenador |
| Fila de Revisão | `/coordenador/revisao` | Coordenador |
| Gestão de Alunos | `/coordenador/alunos` | Coordenador |

---

## 10. Fluxos Principais (User Journeys)

### Aluno — Submissão de Certificado

```
1. Acede a /aluno/enviar
2. Seleciona a Categoria e anexa o PDF (Aluno **não digita** horas)
3. POST /api/academico/certificados/ (multipart/form-data)
4. Backend:
   a. Associa ao AlunoPerfil do utilizador logado
   b. Executa `ocr_service.processar_pdf()` para extrair `horas_sugeridas_ia`
   c. Certificado entra em `revisao_manual` (Paradigma Human-in-the-Loop)
   d. Grava RuleValidationLog (auditoria imutável)
5. Aluno vê atualização no Dashboard e Histórico
```

### Coordenador — Revisão Manual

```
1. Acede a /coordenador/revisao
2. Seleciona certificado → CertificadoDrawer abre
3. Lê o PDF no iframe, analisa metadados
4. Preenche horas validadas + motivo
5. Clica "Deferir" ou "Indeferir"
6. PATCH /api/academico/certificados/{id}/avaliar/
7. Dashboard do aluno reflete novo estado
```

---

## 11. Motor de Regras (Rule Engine)

> **Princípio:** "O Rule Engine decide. O OCR apenas extrai. O Regex apenas higieniza. Todo cálculo deve ser reproduzível e auditável."

**Ficheiros-chave:** `rule_engine/validator.py` e `services/ocr_service.py`

```python
# Fluxo simplificado de processar_certificado()

# 1. Consulta saldo atual do aluno na categoria
saldo_atual = Certificado.objects.filter(
    aluno_id=perfil_id,
    categoria=certificado.categoria,
    status='aprovado'
).aggregate(total=Sum('horas_computadas_final'))['total'] or 0

# 2. Aplica RN03 — Teto por categoria
espaco_disponivel = categoria.limite_maximo_horas - saldo_atual
horas_aprovadas   = min(horas_ocr, espaco_disponivel)
horas_descartadas = horas_ocr - horas_aprovadas

# 3. Grava log de auditoria (imutável)
RuleValidationLog.objects.create(...)
```

---

## 12. Infraestrutura de Testes — Fábrica Sintética

**Ficheiro:** `academico/management/commands/gerar_dataset.py`

Gera PDFs sintéticos ultra-realistas para validar o OCR e o Motor de Regras, sem usar dados reais (conformidade LGPD).

### Tipos de documento

| Tipo | Orientação | Características |
|---|---|---|
| `certificado` | A4 Landscape | 2 sub-layouts (bordas duplas / blocos em colunas), Times-Bold |
| `declaracao` | A4 Portrait | Fundo PNG timbrado, texto justificado via `Paragraph+Frame`, CNPJ fictício no corpo |

### Stress para OCR/Regex

- 3 variações de frase de certificação com estruturas sintáticas distintas
- 3 variações de texto burocrático formal
- Código de validação falso no rodapé (`Courier 7pt`)
- Múltiplos templates de fundo via `glob` (`certificado_bg*.png`)

### Segurança idempotente

- Apaga fisicamente `sintetico_*` e `dummy_*` de `uploads_alunos/`
- Sincroniza o BD removendo registos com `icontains=sintetico/dummy`
- **Nunca** toca em certificados `aprovado` ou `rejeitado`

```bash
python manage.py gerar_dataset
python manage.py gerar_dataset --aluno x@unitins.br
python manage.py gerar_dataset --qtd 3
```

---

## 13. Guia de Configuração e Desenvolvimento

### Pré-requisitos

- Python 3.11+, Node.js 18+, PostgreSQL 14+, Redis

### Backend

```bash
cd aacc_plataforma_unitins/backend
python -m venv venv
venv\Scripts\activate           # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_database
python manage.py runserver       # http://127.0.0.1:8000
```

### Frontend

```bash
cd aacc_plataforma_unitins/frontend
npm install
npm run dev                      # http://localhost:5173
```

---

## 14. Variáveis de Ambiente

Ficheiro: `backend/.env` (não versionado)

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True

DB_NAME=aacc_db
DB_USER=postgres
DB_PASSWORD=sua-senha
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0
```

---

## 15. Comandos de Gestão Django

| Comando | Descrição |
|---|---|
| `python manage.py migrate` | Aplica migrações |
| `python manage.py seed_database` | Popula o banco com dados de teste (alunos, certificados variados) |
| `python manage.py gerar_dataset` | Gera PDFs sintéticos ultra-realistas (`pendente_ocr`) |
| `python manage.py gerar_dataset --aluno x@unitins.br` | Dataset para aluno específico |
| `python manage.py gerar_dataset --qtd N` | Quantidade fixa de documentos por aluno |
| `python manage.py createsuperuser` | Cria administrador para `/admin/` |
| `python manage.py shell` | Shell interativo com contexto Django |

---

## 16. Decisões de Design e Filosofia

### Backend

- **Separação de responsabilidades:** `rule_engine/` é independente da camada de views. A lógica de negócio nunca vive numa view.
- **Auditabilidade total:** Todo certificado processado gera um `RuleValidationLog` imutável com justificativa e artigo da resolução.
- **Segurança por defeito:** `get_queryset` é blindado por papel — alunos nunca recebem dados de outros alunos.
- **Zero I/O temporário:** `gerar_dataset` usa `io.BytesIO` exclusivamente — sem ficheiros temporários em disco.

### Frontend

- **DRY:** `ExtratoCharts.jsx` é partilhado entre o Dashboard do Aluno e o RaioX do Coordenador.
- **Design System centralizado:** Tokens em `global.css` como variáveis CSS, consumidas pelo Tailwind.
- **Componentização Atómica:** `atoms/` → `organisms/` → `pages/`.

### Geral

- **LGPD:** A fábrica sintética nunca usa dados reais. Todos os documentos são gerados por `Faker`.
- **Acessos institucionais:** Apenas e-mails `@unitins.br` são aceites.

---

## 17. Roadmap — Funcionalidades Pendentes

### Curto prazo

| Feature | Descrição |
|---|---|
| **Detecção de Duplicatas (RN04)** | Hash SHA-256 do PDF no upload para bloquear documentos idênticos. |
| **Requerimento Final (RN06)** | Gerar PDF do "Anexo I" para alunos com `apto_formatura=True`. |

### Médio prazo

| Feature | Descrição |
|---|---|
| **Notificações** | E-mails automáticos (Celery) ao aluno quando o status muda. |
| **Relatórios** | Dashboard analítico com estatísticas da turma (taxa de aprovação, eixos mais populares). |
| **Gestão de Categorias** | CRUD de categorias AACC pela interface do coordenador. |

### Longo prazo

| Feature | Descrição |
|---|---|
| **Containerização** | Docker Compose completo (Django + PostgreSQL + Redis + Celery + Nginx). |
| **CI/CD** | Pipeline com GitHub Actions para deploy automatizado. |
| **Mobile** | React Native para submissão via câmera. |

---

*AACC Platform · Desenvolvido para UNITINS — Sistemas de Informação · Resolução CONSUNI nº 057/2025 · v0.1.0*
