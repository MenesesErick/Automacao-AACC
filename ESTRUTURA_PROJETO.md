# Estrutura de Diretórios do Projeto — Automacao-AACC

```text
Automacao-AACC/
│
├── aacc_plataforma_unitins/                  # Diretório principal da aplicação Full-Stack
│   ├── backend/                              # API RESTful, Motor SEBR e Pipeline OCR (Django/DRF)
│   │   ├── aacc_core/                        # Configurações globais (settings.py, urls.py, wsgi.py)
│   │   ├── accounts/                         # Autenticação stateless JWT e controle de acesso (RBAC)
│   │   ├── academico/                        # Núcleo de domínio das AACC (Models, Views e Serializers)
│   │   │   ├── services/                     # Visão Computacional (ocr_service.py) e Avaliação (avaliacao_service.py)
│   │   │   ├── rules/                        # Motor de Inferência SEBR (resolucao_057.py / CalculadoraLimites)
│   │   │   └── management/                   # Gerador sintético (gerador_certificados.py) e comandos de experimento
│   │   ├── media/                            # Templates de fundo (templates_base/) e uploads de alunos
│   │   ├── resultados_tcc/                   # Gráficos científicos gerados (CER por nível e eficácia RN04)
│   │   ├── scripts/                          # Utilitários de extração normativa (atualizar_regras_pdf.py)
│   │   ├── avaliar_ocr_tcc.py                # Script de aferição estatística (CER, WER, FAR e trava RN04)
│   │   ├── relatorio_dataset_massivo.json    # Ground Truth e resultados da simulação de 300 documentos
│   │   └── requirements.txt                  # Dependências do ambiente Python
│   │
│   ├── frontend/                             # Aplicação SPA (React 18 + Vite + Tailwind CSS)
│   │   └── src/                              # Páginas por perfil, Copiloto Pré-Submissão, Split-Screen e AnexoIPDF
│   │
│   └── docker-compose.yml                    # Orquestração opcional de banco PostgreSQL 15 e pgAdmin 4
│
├── documentos_comprobatorios_300/            # Dataset sintético estratificado (300 PDFs Níveis 1, 2 e 3)
├── .gitignore                                # Exclusão de ambientes virtuais, caches e variáveis sensíveis
├── Contexto.md                               # Especificação de domínio e regras de negócio (RN01 a RN06)
└── README.md                                 # Documentação técnica, arquitetura e guia de execução
```
