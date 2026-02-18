🚀 Projeto: TradeJournal (Micro-SaaS)
🎯 1. O Objetivo (A Dor e a Solução)
O desenvolvimento do TradeJournal nasceu da necessidade de resolver um problema real de traders: a dificuldade de analisar performance de forma rápida e visual.
A maioria dos traders perde tempo preenchendo planilhas manuais ou operando "no escuro".
O objetivo deste projeto foi criar uma plataforma Full Stack que:

Automatiza a ingestão de dados (lendo relatórios complexos do Excel do MetaTrader 5).

Democratiza a análise profissional com um modelo de negócio Freemium (SaaS).

Transforma dados brutos em inteligência visual (Gráficos de Patrimônio, Drawdown, Fator de Lucro).

Demonstra capacidade técnica de construir um produto do zero ao deploy (End-to-End).

🛠️ 2. Stack Tecnológico (O "Como")
O projeto foi construído utilizando uma arquitetura robusta e escalável, focada em Python para o processamento de dados e Flask para a web.

Backend & API:

Python 3.13: Linguagem core.

Flask: Framework web leve e modular.

SQLAlchemy (ORM): Para modelagem e interação segura com o banco de dados.

Werkzeug: Para segurança (hash de senhas e tratamento de arquivos).

Data Science & Analytics:

Pandas: O coração do sistema. Utilizado para ler arquivos .xlsx, limpar dados, calcular vetores financeiros e gerar estatísticas complexas em milissegundos.

NumPy: Auxiliar em cálculos matemáticos de vetores.

Frontend & UX:

Jinja2: Engine de templates para renderização dinâmica (Server-Side Rendering).

Bootstrap 5: Framework CSS para responsividade e design moderno.

Chart.js: Biblioteca JavaScript para renderização de gráficos interativos e animados (Canvas).

Infraestrutura & Deploy:

PostgreSQL: Banco de dados relacional para produção (Render).

Render Cloud: Plataforma de PaaS para hospedagem da aplicação.

Gunicorn: Servidor WSGI para produção.

⭐ 3. Principais Funcionalidades (O Valor Entregue)
O sistema vai muito além de um simples CRUD. Ele implementa lógicas de negócio complexas:

Engenharia de Dados Financeiros:

Processamento de upload de arquivos Excel.

Cálculo automático de Net Profit, Drawdown (queda máxima), Sequências de Vitórias/Derrotas e Taxa de Acerto.

Lógica SaaS (Software as a Service):

Controle de Acesso (ACL): Diferenciação entre usuários Free e Pro.

Paywall Lógico: Usuários Free têm o histórico limitado visualmente aos últimos 30 dias (regra de negócio aplicada no Backend).

Painel Administrativo ("God Mode"): Área restrita onde o administrador pode visualizar métricas globais, promover ou rebaixar usuários e gerenciar o sistema.

Features de "Journaling" (Diário):

Sistema que permite ao trader clicar em uma operação específica e registrar anotações textuais (psicológico, técnica usada), salvando isso no banco de dados relacional.

Experiência do Usuário (UX):

Landing Page de alta conversão com gráficos animados em tempo real.

Dashboards intuitivos com feedback visual imediato (cores verde/vermelho para lucro/prejuízo).
