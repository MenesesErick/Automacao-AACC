# CONTEXT.md

# Plataforma de Automação de AACC - UNITINS

## Objetivo

Este projeto tem como objetivo desenvolver uma plataforma web capaz de automatizar o processo de validação das Atividades Acadêmicas Complementares (AACC) da Universidade Estadual do Tocantins (UNITINS).

Atualmente o processo é totalmente manual, exigindo que o coordenador analise certificado por certificado, calcule as horas permitidas de acordo com a Resolução CONSUNI nº 057/2025 e preencha manualmente o Anexo I.

O sistema proposto automatiza praticamente todo esse fluxo utilizando OCR, Processamento de Texto e um Motor de Regras determinístico.

---

# O Problema

O processo atual apresenta diversos gargalos:

- Recebimento de certificados por e-mail ou I-Protocolo;
- Organização manual dos documentos;
- Leitura manual de certificados;
- Cálculo manual das horas;
- Conferência constante da Resolução CONSUNI;
- Alto risco de erro humano;
- Sobrecarga da coordenação;
- Falta de rastreabilidade;
- Processo lento.

A proposta do projeto é eliminar essas atividades repetitivas.

---

# Objetivo da Plataforma

A plataforma deve ser capaz de:

- Receber certificados em PDF ou imagem;
- Executar OCR;
- Extrair automaticamente as informações relevantes;
- Identificar a atividade realizada;
- Aplicar automaticamente as regras da Resolução CONSUNI 057/2025;
- Calcular a carga horária válida;
- Detectar horas excedentes;
- Detectar atividades duplicadas;
- Gerar automaticamente o Requerimento de Contabilização (Anexo I);
- Disponibilizar dashboards para alunos e coordenadores.

---

# Público-alvo

## Aluno

O aluno poderá:

- enviar certificados;
- acompanhar horas contabilizadas;
- visualizar pendências;
- consultar horas restantes;
- solicitar revisão.

## Coordenador

O coordenador poderá:

- analisar documentos;
- revisar OCR quando necessário;
- validar atividades;
- acompanhar estatísticas;
- gerar o Anexo I.

## Secretaria Acadêmica

Responsável por:

- registrar horas validadas;
- arquivar documentação;
- atualizar histórico acadêmico.

---

# Tecnologias Principais

## OCR

Responsável pela leitura automática dos certificados.

O OCR extrai informações como:

- Nome
- Carga Horária
- Data
- Instituição
- Evento
- Participante

Caso o OCR apresente baixa confiança, o documento deverá ser encaminhado para revisão humana (Human in the Loop).

---

## Regex

Após o OCR, o texto bruto será higienizado utilizando Expressões Regulares (Regex).

Exemplos:

- localizar carga horária
- localizar datas
- localizar CPF
- localizar nome do participante

---

## Motor de Regras

É o núcleo mais importante da aplicação.

Todo o comportamento da plataforma depende dele.

O Motor de Regras deve ser completamente determinístico.

Nunca utilizar IA para decidir regras acadêmicas.

Toda decisão deve ser baseada na Resolução CONSUNI nº 057/2025.

---

# Fonte da Verdade

A única fonte oficial para validação das horas é:

> Resolução CONSUNI nº 057/2025

Qualquer documento legado deve ser considerado apenas como referência histórica.

Caso exista conflito entre documentos antigos e a resolução, prevalece sempre a Resolução 057/2025.

---

# Grupos de Atividades

Toda atividade pertence a exatamente um grupo.

## Ensino

Exemplos:

- Monitoria
- PIBID
- Disciplinas correlatas
- Cursos

## Pesquisa

Exemplos:

- Iniciação Científica
- Publicações
- Artigos
- Congressos

## Extensão

Exemplos:

- Estágio
- Voluntariado
- Visitas Técnicas
- Representação Discente
- Idiomas

---

# Regras Obrigatórias

A plataforma deve garantir automaticamente:

## RN01

Uma atividade nunca poderá ser contabilizada duas vezes.

---

## RN02

O aluno deve possuir atividades em pelo menos dois grupos diferentes.

---

## RN03

Cada categoria possui limite máximo de horas.

Exemplo:

Monitoria:

Limite: 60h

Se certificado possuir 80h:

Horas validadas = 60h

---

## RN04

As horas excedentes nunca devem ser descartadas silenciosamente.

O sistema deve informar ao aluno:

- Horas enviadas
- Horas aproveitadas
- Horas descartadas
- Motivo

---

## RN05

Todas as decisões do Motor de Regras devem ser auditáveis.

Cada validação deve possuir:

- regra aplicada;
- data;
- usuário;
- justificativa;
- artigo da resolução.

---

# Fluxo Geral

```text
Aluno

↓

Upload do Certificado

↓

OCR

↓

Texto Extraído

↓

Regex

↓

Dados Estruturados

↓

Motor de Regras

↓

Validação

↓

Banco de Dados

↓

Dashboard

↓

Anexo I

↓

Secretaria
```

---

# Human in the Loop

O sistema NÃO deve confiar cegamente no OCR.

Sempre que:

- confiança baixa;
- texto ilegível;
- certificado incompleto;
- múltiplas interpretações;

o documento deverá ser enviado para revisão humana.

---

# Estrutura Geral da Aplicação

```text
Frontend

│

├── Portal do Aluno

├── Portal do Coordenador

└── Portal Administrativo


Backend

│

├── API REST

├── OCR Service

├── Parser

├── Regex Engine

├── Rule Engine

├── Notification Service

├── Audit Service

└── Report Service


Banco

│

├── Alunos

├── Cursos

├── Certificados

├── OCR

├── Regras

├── Validações

├── Logs

├── Auditoria

└── Histórico
```

---

# Entidades Principais

- Aluno
- Curso
- Certificado
- Categoria
- Grupo
- OCRResult
- RuleValidation
- Requerimento
- Usuário
- Log
- Auditoria

---

# Funcionalidades Esperadas

## Aluno

- Login
- Upload
- Histórico
- Horas
- Pendências

## Coordenador

- Dashboard
- Revisão OCR
- Aprovação
- Rejeição
- Estatísticas

## Secretaria

- Registro
- Histórico
- Exportação

---

# Arquitetura

A arquitetura deve ser modular.

Cada serviço deve possuir responsabilidade única.

Evitar regras de negócio espalhadas pelo sistema.

Toda lógica referente à Resolução deve permanecer centralizada no Rule Engine.

---

# Princípios do Projeto

- Código limpo
- SOLID
- Arquitetura em camadas
- Separação entre OCR e Rule Engine
- Regras configuráveis
- Fácil manutenção
- Alta rastreabilidade
- Auditoria completa
- Escalabilidade
- Segurança
- LGPD

---

# Futuras Evoluções

- Integração com RM
- Integração com I-Protocolo
- Assinatura Digital
- OCR baseado em IA
- Dashboard BI
- Exportação PDF
- API pública
- Aplicativo Mobile

---

# Observações Importantes para IA

Ao gerar código para este projeto:

- Nunca criar regras acadêmicas sem base na Resolução.
- Nunca utilizar IA para calcular horas.
- Sempre considerar o Rule Engine como responsável pelas decisões.
- O OCR apenas extrai texto.
- Regex apenas higieniza dados.
- O Rule Engine decide.
- O Coordenador possui a decisão final quando houver exceções.
- Todo cálculo deve ser reproduzível e auditável.
- O sistema deve priorizar confiabilidade em vez de automação total.