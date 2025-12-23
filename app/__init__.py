from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Cria a instância da aplicação (o objeto que representa o site)
app = Flask(__name__)

# --- CONFIGURAÇÕES DE SEGURANÇA E BANCO ---
# Chave secreta para proteger os cookies de sessão (em produção, isso fica oculto)
app.config['SECRET_KEY'] = 'uma-senha-muito-secreta-do-projeto-trade'

# Onde o arquivo do banco vai ficar (app.db na pasta app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa as extensões
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login' # Se alguém tentar acessar página restrita, vem pra cá

# Importa as rotas (atenção: deve ser importado DEPOIS de criar o app para evitar erro circular)
from app import routes, models