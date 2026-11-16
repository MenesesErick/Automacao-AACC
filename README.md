# Plataforma AACC — Automação e Validação de Atividades Complementares (UNITINS)

> **Universidade Estadual do Tocantins — UNITINS**  
> **Curso:** Sistemas de Informação · **Regulamentação Base:** Resolução CONSUNI/UNITINS nº 057/2025  
> **Arquitetura:** Full-Stack (Django REST Framework + React/Vite + Pipeline OCR Híbrido + Motor de Regras Determinístico SEBR)

---

## Sumário

1. [Sobre o Projeto](#1-sobre-o-projeto)
2. [Principais Funcionalidades e Regras de Negócio](#2-principais-funcionalidades-e-regras-de-negócio)
3. [Arquitetura e Fluxo de Funcionamento](#3-arquitetura-e-fluxo-de-funcionamento)
4. [Dependências e Requisitos do Sistema](#4-dependências-e-requisitos-do-sistema)
5. [Mini-Tutorial: Como Rodar em Outra Máquina (Passo a Passo)](#5-mini-tutorial-como-rodar-em-outra-máquina-passo-a-passo)
6. [Credenciais de Teste (Geradas pelo Seed)](#6-credenciais-de-teste-geradas-pelo-seed)
7. [Executando o Benchmark Estatístico do TCC (300 Documentos)](#7-executando-o-benchmark-estatístico-do-tcc-300-documentos)
8. [Estrutura de Diretórios](#8-estrutura-de-diretórios)
9. [Principais Endpoints da API REST](#9-principais-endpoints-da-api-rest)
10. [Comandos Úteis do Django](#10-comandos-úteis-do-django)

---

## 1. Sobre o Projeto

As **Atividades Acadêmico-Científico-Culturais (AACC)** são requisito curricular obrigatório para a colação de grau nos cursos de graduação da **UNITINS**, regulamentadas pela **Resolução CONSUNI nº 057/2025**. Os acadêmicos devem cumprir a carga horária exigida pela sua matriz curricular (ex.: **120h** ou **180h**) distribuída entre os eixos formativos de **Ensino**, **Pesquisa** e **Extensão**.

### O Problema
No fluxo tradicional, o envio de certificados, a leitura de carga horária, a verificação de titularidade, o cálculo de tetos por atividade/categoria e o preenchimento do **Requerimento de Contabilização (Anexo I)** ocorrem manualmente, gerando sobrecarga para as coordenações de curso, lentidão no parecer e risco de erros de cálculo.

### A Solução
A **Plataforma AACC** digitaliza e automatiza o ciclo completo em paradigma **Human-in-the-Loop**:
1. **Copiloto de Pré-Submissão (Aluno):** Ao anexar o PDF/imagem do certificado, o sistema extrai automaticamente **Título da Atividade**, **Período de Realização**, **Carga Horária** e valida a **Titularidade (Nome do Discente)** antes mesmo do envio definitivo, permitindo ao aluno revisar e ajustar os dados.
2. **Pipeline OCR Híbrido (PyMuPDF + Tesseract + Motor de Consenso Regex):** Extrai o texto nativo de PDFs vetoriais (Fase 1) e aplica fallback automático de rasterização a 300 DPI + OCR via **Tesseract** para documentos escaneados ou fotografados (Fase 2).
3. **Motor de Regras Determinístico (SEBR — Resolução 057/2025):** Calcula os limites por certificado/evento e tetos máximos por categoria, registrando a memória de cálculo auditável (`RuleValidationLog`) sem descartar horas silenciosamente.
4. **Mesa de Avaliação do Coordenador & Geração do Anexo I:** Permite ao coordenador auditar lado a lado o PDF original e os metadados extraídos, deferir/indeferir com um clique e emitir o **Anexo I oficial em PDF** assim que o aluno atingir a meta de horas e a diversificação mínima de eixos.

---

## 2. Principais Funcionalidades e Regras de Negócio

Todas as decisões acadêmicas seguem estritamente a **Resolução CONSUNI nº 057/2025**:

| Código | Regra / Funcionalidade | Descrição Técnica |
|:------:|:-----------------------|:------------------|
| **RN01** | **Extração OCR Híbrida + Consenso** | Extração textual via `PyMuPDF` (camada nativa) com fallback para `pytesseract` (imagens/PDFs achatados) e votação de carga horária por consenso de padrões Regex. |
| **RN02** | **Diversificação de Eixos Formativos** | Para estar apto à formatura e liberar a emissão do **Anexo I**, o aluno deve simultaneamente atingir a meta da matriz (`total_horas >= meta_horas`) **E** possuir horas validadas em **pelo menos 2 eixos distintos** (`Ensino`, `Pesquisa`, `Extensão`). |
| **RN03** | **Tetos por Evento e por Categoria** | O motor SEBR (`resolucao_057.py`) aplica automaticamente o limite máximo por certificado (`teto_por_evento`) e o limite acumulado na categoria (`teto_total`), exigindo justificativa em caso de indeferimento. |
| **RN04** | **Dupla Checagem de Titularidade e Trava Cognitiva** | Compara o nome extraído no documento com o nome do aluno logado via similaridade fuzzy (`SequenceMatcher`). Se a titularidade não for confirmada (`similaridade < 80%`), aplica-se a trava `confianca_ocr = min(confianca_ocr, 65%)`, acionando o alerta de revisão manual rigorosa para o coordenador. |
| **RN05** | **Auditoria Imutável & Human-in-the-Loop** | Todo certificado passa pela curadoria final da coordenação e gera registros imutáveis em `RuleValidationLog` (horas enviadas, horas computadas, horas descartadas e artigo da resolução). |
| **RN06** | **Isolamento por Curso e Emissão do Anexo I** | Coordenadores visualizam exclusivamente os alunos e certificados do seu curso e emitem o **Anexo I** oficial (`AnexoIPDF.jsx` / `GerarAnexoIView`) com as cargas horárias originais e validadas. |

---

## 3. Arquitetura e Fluxo de Funcionamento

```text
+-------------------------------------------------------------------------+
|                            Plataforma AACC                              |
|                                                                         |
|  +------------------------+     REST / JWT     +---------------------+  |
|  |   Frontend (SPA)       | <================> |  Backend (API)      |  |
|  |   React 18 + Vite 5    |   JSON / FormData  |  Django 4.2 + DRF   |  |
|  |   Tailwind CSS 3       |                    |  SQLite / Postgres  |  |
|  +------------------------+                    +---------------------+  |
|        Porta :5173                                   Porta :8000        |
|                                                           |             |
|                         +---------------------------------+             |
|                         |                                               |
|                         v                                               |
|  +-------------------------------------------------------------------+  |
|  | Núcleo do Backend                                                 |  |
|  |  - accounts/       -> Autenticação JWT e Perfis (Admin/Coord/Aluno)|  |
|  |  - academico/      -> Certificados, Extrato, Dossiê, Anexo I      |  |
|  |  - ocr_service.py  -> PyMuPDF + Pillow + Tesseract + Titularidade |  |
|  |  - resolucao_057.py-> Motor Determinístico SEBR (Tetos e Regras)  |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 4. Dependências e Requisitos do Sistema

### 4.1. Requisitos Globais da Máquina
- **Git** (para clonar e versionar o repositório)
- **Python 3.11 ou superior** (compatível até Python 3.14)
- **Node.js 18+ e npm** (para rodar o frontend React/Vite)
- **Tesseract OCR** *(Opcional para PDFs digitais nativos; **Obrigatório** para leitura OCR de imagens `.jpg`/`.png` e PDFs escaneados de Nível 2 e 3)*
  - **Windows:** Baixe o instalador em [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) e marque o idioma **Portuguese (`por`)** durante a instalação (caminho padrão: `C:\Program Files\Tesseract-OCR\tesseract.exe`).
  - **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install -y tesseract-ocr tesseract-ocr-por`
  - **macOS (Homebrew):** `brew install tesseract tesseract-lang`
- **Banco de Dados:**
  - Por padrão, em desenvolvimento local, o sistema utiliza **SQLite (`db.sqlite3`)** automaticamente caso `DATABASE_URL` não seja informada — **não é necessário instalar banco externo para testar rapidamente**.
  - Caso deseje rodar com **PostgreSQL 15 + pgAdmin 4**, há um arquivo `docker-compose.yml` pronto no projeto.

### 4.2. Principais Dependências do Backend (`backend/requirements.txt`)
| Pacote | Versão | Finalidade |
|:-------|:------:|:-----------|
| `Django` | `4.2.30` | Framework web principal e ORM |
| `djangorestframework` | `3.17.1` | Construção da API RESTful |
| `djangorestframework_simplejwt` | `5.5.1` | Autenticação stateless via tokens JWT (Bearer) |
| `django-cors-headers` | `4.9.0` | Liberação segura de CORS entre Frontend e Backend |
| `python-decouple` / `dj-database-url` | `3.8` / `3.1.2` | Leitura de variáveis de ambiente (`.env`) e conexão de banco |
| `pymupdf` (`fitz`) | `1.28.0` | Extração nativa de texto de PDFs e rasterização de páginas |
| `pytesseract` | `0.3.13` | Wrapper Python para o motor Tesseract OCR |
| `pillow` | `12.3.0` | Manipulação e pré-processamento de imagens em memória |
| `reportlab` / `xhtml2pdf` | `5.0.0` / `0.2.20` | Geração de certificados sintéticos realistas e relatórios PDF |
| `psycopg2-binary` | `2.9.12` | Driver para conexão com PostgreSQL |
| `Faker` | `40.31.0` | Geração de dados sintéticos em conformidade com a LGPD |
| `jiwer` / `matplotlib` | — | Cálculo de métricas científicas (CER/WER) e gráficos do TCC |

### 4.3. Principais Dependências do Frontend (`frontend/package.json`)
| Pacote | Versão | Finalidade |
|:-------|:------:|:-----------|
| `react` / `react-dom` | `^18.3.1` | Biblioteca de construção da interface de usuário |
| `vite` | `^5.3.1` | Servidor de desenvolvimento rápido (HMR) e bundler |
| `tailwindcss` | `^3.4.4` | Estilização padronizada com identidade visual da UNITINS |
| `react-router-dom` | `^6.24.0` | Roteamento SPA e proteção de rotas por perfil |
| `axios` | `^1.7.2` | Cliente HTTP com interceptors automáticos de JWT |
| `lucide-react` | `^0.395.0` | Ícones consistentes na interface |
| `recharts` | `^3.9.2` | Gráficos de progresso de horas e distribuição por eixos |
| `react-to-print` | `^3.3.0` | Impressão/exportação fiel do Requerimento Anexo I em PDF |
| `sonner` | `^2.0.8` | Notificações estilo toast em tempo real |
| `jwt-decode` | `^4.0.0` | Decodificação do token JWT no cliente |

---

## 5. Mini-Tutorial: Como Rodar em Outra Máquina (Passo a Passo)

Siga os passos abaixo para subir todo o ambiente (Backend + Banco de Dados + Dados de Teste + Frontend) em qualquer computador novo:

### Passo 1 — Clonar o Repositório

```bash
git clone https://github.com/MenesesErick/Automacao-AACC.git
cd Automacao-AACC
```

---

### Passo 2 — Configurar e Rodar o Backend (Django)

Abra um terminal na raiz do projeto e entre na pasta do backend:

```bash
cd aacc_plataforma_unitins/backend
```

#### 2.1. Criar e ativar o ambiente virtual (`venv`)
- **No Windows (PowerShell ou CMD):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **No Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

#### 2.2. Instalar as dependências Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install jiwer matplotlib
```

#### 2.3. Criar o arquivo `.env` no Backend
Crie um arquivo chamado `.env` dentro de `aacc_plataforma_unitins/backend/.env` com o seguinte conteúdo:

```env
SECRET_KEY=chave-secreta-desenvolvimento-unitins-aacc-2026
DEBUG=True

# Opcional: caminho do executável do Tesseract no Windows (caso não esteja no PATH global)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Opcional: descomente a linha abaixo APENAS se quiser usar PostgreSQL via Docker em vez do SQLite padrão
# DATABASE_URL=postgres://aacc_user:aacc_pass@localhost:5432/aacc_db
```

> **Dica:** Se você deixar `DATABASE_URL` comentado ou vazio, o Django criará e usará automaticamente o banco local `db.sqlite3` sem precisar configurar o PostgreSQL.  
> Caso prefira usar PostgreSQL via Docker, basta executar `docker compose up -d` na pasta `aacc_plataforma_unitins/` antes de rodar as migrações.

#### 2.4. Executar as migrações e popular o banco com dados de teste
```bash
python manage.py migrate
python manage.py setup_test_data
```
*(O comando `setup_test_data` cria automaticamente os 3 eixos formativos, todas as categorias da Resolução 057/2025, o curso de Sistemas de Informação com matrizes de 120h e 180h, as contas de Admin, Coordenador e 8 Alunos com certificados PDF sintéticos prontos para teste!)*

#### 2.5. Iniciar o servidor do Backend
```bash
python manage.py runserver
```
O backend estará disponível em: **`http://127.0.0.1:8000`**

---

### Passo 3 — Configurar e Rodar o Frontend (React + Vite)

Abra um **segundo terminal** (mantenha o terminal do backend rodando) e acesse a pasta do frontend:

```bash
cd aacc_plataforma_unitins/frontend
```

#### 3.1. Instalar os pacotes Node.js
```bash
npm install
```

#### 3.2. Iniciar o servidor de desenvolvimento Vite
```bash
npm run dev
```
O frontend estará disponível em: **`http://localhost:5173`**

---

## 6. Credenciais de Teste (Geradas pelo Seed)

Após rodar `python manage.py setup_test_data`, utilize qualquer uma das contas abaixo na tela de login (`http://localhost:5173/login`).  
A senha padrão para **todos** os usuários de teste é: **`unitins2026`**

| Perfil | E-mail (Login) | Senha | Matriz / Curso |
|:------:|:---------------|:-----:|:---------------|
| **Administrador** | `admin@unitins.br` | `unitins2026` | Acesso global (Cursos, Eixos, Categorias, Coordenadores) |
| **Coordenador** | `coord@unitins.br` | `unitins2026` | Coordenador de Sistemas de Informação |
| **Aluno (120h)** | `erick.meneses@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 120h |
| **Aluno (120h)** | `joao.silva@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 120h |
| **Aluno (120h)** | `maria.souza@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 120h |
| **Aluno (120h)** | `beatriz.lima@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 120h |
| **Aluno (180h)** | `pedro.santos@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 180h |
| **Aluno (180h)** | `ana.costa@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 180h |
| **Aluno (180h)** | `lucas.ferreira@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 180h |
| **Aluno (180h)** | `gabriel.rocha@unitins.br` | `unitins2026` | Sistemas de Informação — Matriz 180h |

---

## 7. Executando o Benchmark Estatístico do TCC (300 Documentos)

O projeto conta com um motor de benchmark 100% em memória (`io.BytesIO`) para validação científica do pipeline de OCR e da trava de segurança **RN04** (Capítulo 4 do TCC), gerando 300 documentos estratificados em:
- **60% Nível 1:** PDFs vetoriais nativos;
- **25% Nível 2:** PDFs achatados/rasterizados a 200 DPI (sem camada textual, exigindo Tesseract OCR);
- **15% Nível 3:** PDFs com degradação severa (distorção de perspectiva keystone, rotação, desfoque gaussiano, variação de brilho/contraste, compressão JPEG `quality=15` e anomalias de caracteres).

Para reproduzir o experimento completo no terminal (dentro de `aacc_plataforma_unitins/backend` com a `venv` ativa):

```bash
# 1. Gera os 300 documentos em memória, processa no OCR e exporta relatorio_dataset_massivo.json
python manage.py gerar_experimento_tcc

# 2. Calcula CER, WER, Acurácia de Horas, eficácia da Trava RN04 e gera os gráficos em resultados_tcc/
python avaliar_ocr_tcc.py
```

Os gráficos gerados em alta resolução (300 DPI) ficam salvos em:
- `aacc_plataforma_unitins/backend/resultados_tcc/grafico1_cer_por_nivel.png`
- `aacc_plataforma_unitins/backend/resultados_tcc/grafico2_eficacia_rn04_nivel3.png`

---

## 8. Estrutura de Diretórios

```text
Automacao-AACC/
├── README.md                              ← Documentação principal e tutorial de execução
├── Contexto.md                            ← Especificação de domínio e regras de negócio
├── documentos_comprobatorios_300/         ← Dataset sintético (300 PDFs Níveis 1, 2 e 3)
│
└── aacc_plataforma_unitins/
    ├── docker-compose.yml                 ← PostgreSQL 15 + pgAdmin 4 (opcional)
    │
    ├── backend/                           ← API Django REST Framework
    │   ├── manage.py
    │   ├── requirements.txt               ← Dependências Python
    │   ├── avaliar_ocr_tcc.py             ← Avaliador científico (CER/WER/FAR/RN04 + gráficos)
    │   ├── relatorio_dataset_massivo.json ← Dataset resultante do experimento de 300 docs
    │   ├── resultados_tcc/                ← Gráficos gerados pelo avaliador
    │   ├── media/                         ← Templates de fundo (templates_base/) e uploads
    │   ├── scripts/                       ← Utilitários (atualizar_regras_pdf.py)
    │   ├── aacc_core/                     ← Configurações globais (settings.py, urls.py)
    │   ├── accounts/                      ← Autenticação JWT e modelo customizado Usuario
    │   └── academico/                     ← App principal do domínio AACC
    │       ├── models.py                  ← Eixo, Curso, Matriz, CategoriaAACC, Certificado, Log
    │       ├── serializers.py             ← Serializers DRF
    │       ├── views.py                   ← ViewSets, AnalisePreviaView, Extrato, GerarAnexoIView
    │       ├── rules/
    │       │   └── resolucao_057.py       ← Motor SEBR (Regras e tetos da Resolução 057/2025)
    │       ├── services/
    │       │   ├── ocr_service.py         ← Extrator híbrido PyMuPDF + Tesseract + Titularidade
    │       │   └── avaliacao_service.py   ← Deferimento/Indeferimento com memória de cálculo
    │       └── management/
    │           ├── gerador_certificados.py        ← Fábrica sintética ReportLab (Níveis 1, 2 e 3)
    │           └── commands/
    │               ├── setup_test_data.py         ← Povoamento completo de usuários e certificados
    │               ├── gerar_experimento_tcc.py   ← Benchmark in-memory de 300 documentos
    │               └── popular_categorias.py      ← Sincronização das categorias da Resolução
    │
    └── frontend/                          ← Aplicação React + Vite + Tailwind CSS
        ├── package.json
        ├── vite.config.js
        ├── tailwind.config.js
        └── src/
            ├── components/
            │   ├── AnexoIPDF.jsx          ← Template oficial de impressão do Anexo I
            │   ├── layout/                ← AppLayout, Sidebar, Header, NotificationBell
            │   └── organisms/             ← Modais e componentes compostos
            ├── contexts/
            │   └── AuthContext.jsx        ← Gestão de sessão e autenticação JWT
            ├── pages/
            │   ├── auth/                  ← Login e Cadastro de Aluno
            │   ├── aluno/                 ← DashboardAluno, SubmeterCertificado, HistoricoAluno
            │   ├── coordenador/           ← MesaAvaliacao, AvaliarCertificado, DossieAluno
            │   └── admin/                 ← Gestão de Cursos, Eixos, Categorias e Coordenadores
            └── services/api/
                ├── client.js              ← Instância Axios com injeção e refresh de token JWT
                └── endpoints.js           ← Mapeamento de todos os serviços da API
```

---

## 9. Principais Endpoints da API REST

**URL Base Local:** `http://127.0.0.1:8000/api/`

| Método | Endpoint | Acesso | Descrição |
|:------:|:---------|:------:|:----------|
| `POST` | `/accounts/token/` | Público | Autenticação (retorna tokens `access` e `refresh`) |
| `GET` | `/accounts/me/` | Autenticado | Dados e papel do usuário logado |
| `GET` | `/academico/categorias/` | Autenticado | Lista categorias AACC agrupadas por eixo formativo |
| `POST` | `/academico/certificados/analise-previa/` | Aluno | **Copiloto Pré-Submissão:** extrai título, período, carga horária (`horas_sugeridas`) e titularidade sem salvar no banco |
| `GET` / `POST` | `/academico/certificados/` | Aluno / Coord. | Lista certificados ou submete novo certificado com `horas_declaradas` revisadas |
| `PATCH` | `/academico/certificados/{id}/avaliar/` | Coordenador | Deferir (`acao: "aprovar"`) ou indeferir (`acao: "rejeitar"`) aplicando o motor SEBR |
| `GET` | `/academico/alunos/meu-extrato/` | Aluno | Progresso de horas por eixo, meta da matriz e elegibilidade |
| `GET` | `/academico/alunos/{id}/extrato/` | Coordenador | Extrato detalhado de um aluno específico |
| `GET` | `/academico/alunos/{id}/gerar-anexo-i/` | Coordenador | Valida meta + diversificação (mínimo 2 eixos) e retorna o JSON oficial para emissão do Anexo I |

---

## 10. Comandos Úteis do Django

Execute sempre dentro de `aacc_plataforma_unitins/backend` com o ambiente virtual (`venv`) ativo:

| Comando | O que faz |
|:--------|:----------|
| `python manage.py migrate` | Cria ou atualiza as tabelas do banco de dados |
| `python manage.py setup_test_data` | Limpa dados de teste anteriores e recria categorias, coordenador, 8 alunos e certificados PDF sintéticos |
| `python manage.py popular_categorias` | Sincroniza apenas os eixos e categorias da Resolução CONSUNI nº 057/2025 |
| `python manage.py gerar_experimento_tcc --total 300 --seed 42` | Executa o benchmark estatístico de 300 documentos 100% em memória |
| `python avaliar_ocr_tcc.py` | Processa `relatorio_dataset_massivo.json`, exibe as tabelas de CER/WER/RN04 e salva os gráficos em `resultados_tcc/` |
| `python manage.py createsuperuser` | Cria manualmente um novo superusuário administrador |

---

*Plataforma AACC · Universidade Estadual do Tocantins (UNITINS) — Curso de Sistemas de Informação · Resolução CONSUNI nº 057/2025*
