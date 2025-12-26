from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Cria a instância da aplicação (o objeto que representa o site)
app = Flask(__name__)

# --- CONFIGURAÇÃO INTELIGENTE DE BANCO DE DADOS ---
# Tenta pegar a URL do banco das variáveis de ambiente do sistema (no Render)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Correção para o Render: O Render fornece "postgres://", mas o SQLAlchemy exige "postgresql://"
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Se não encontrar a variável (estamos no pc local), usa o SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa as extensões
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login' # Se alguém tentar acessar página restrita, vem pra cá

# Importa as rotas (atenção: deve ser importado DEPOIS de criar o app para evitar erro circular)
from app import routes, models