Arquitetura e Contexto: Plataforma AACC - Unitins
1. Visão Geral
Sistema de automação para análise, cômputo e validação de Atividades Acadêmicas Científicas e Culturais (AACC), baseado na Resolução CONSUNI Nº 057/2025. Substitui o processo analógico de entrega de PDFs por um pipeline inteligente com OCR (Tesseract) e um Motor de Regras Matemáticas.

2. Regras de Negócio Críticas (Obrigatórias para o TCC)
RN01 (Anti-duplicidade): Nenhum certificado pode ser submetido duas vezes. Requer a geração e validação de um hash (SHA-256) do ficheiro PDF no momento do upload.

RN02 (Diversidade de Eixos): Para formar as 120h (ou 180h) necessárias para formatura, as atividades do aluno devem contemplar pelo menos dois eixos distintos (Ensino, Pesquisa ou Extensão). Um aluno não pode atingir a carga total num único eixo.

RN03 (Limites de Teto por Categoria): O sistema deve cortar horas excedentes. Ex: Se "Monitoria" permite até 40h e o aluno tem um saldo de 30h, um novo certificado de 20h só pode aprovar 10h (descartando o resto). [Status: Implementado no rule_engine].

RN04 (Trava de Confiança OCR): O motor de IA extrai as horas. Se o índice de confiança da extração for < 70%, o cômputo automático é bloqueado e o status muda para revisao_manual.

RN05 (Auditoria / Human-in-the-Loop): O Coordenador de Curso tem a palavra final. Ele pode aceder aos casos revisao_manual através do RuleValidationLog, visualizar o PDF lado-a-lado com os dados extraídos, e deferir/indeferir a carga horária.

RN06 (Geração do Requerimento Final): Quando o aluno atinge os requisitos, o sistema gera o "Anexo I" (PDF oficial formatado) compilando todas as horas validadas para entrega na Secretaria Acadêmica.

3. Dívida Técnica Atual (Roadmap Imediato)
Infraestrutura de Arquivos (MEDIA_ROOT): O backend (Django) não está configurado para salvar e servir PDFs em disco. Isso bloqueia a integração do OCR.

Autenticação e Segurança (JWT): Atualmente, o frontend usa "mock auth". É urgente integrar o djangorestframework-simplejwt. A API GET /certificados/ vaza dados de todos os alunos e precisa ser blindada usando request.user.

Relacionamento Aluno-Usuário: Garantir que o upload via POST associe corretamente o documento ao AlunoPerfil do utilizador logado.
