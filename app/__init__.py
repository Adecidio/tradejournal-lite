from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Cria a instância da aplicação (o objeto que representa o site)
app = Flask(__name__)

# --- SEGURANÇA ---
# Tenta pegar do Render (os.environ). Se não achar, usa a string fixa (para rodar no PC).
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# --- BANCO DE DADOS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
# Inicializa as extensões
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login' # Se alguém tentar acessar página restrita, vem pra cá

# Importa as rotas (atenção: deve ser importado DEPOIS de criar o app para evitar erro circular)
from app import routes, models