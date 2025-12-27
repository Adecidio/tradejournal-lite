from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# --- DEBUG TEMPORÁRIO ---
print("--- INICIANDO APP ---")
key_render = os.environ.get('SECRET_KEY')
if key_render:
    print(f"Chave encontrada: {key_render[:5]}...")
else:
    print("ERRO CRÍTICO: Nenhuma SECRET_KEY encontrada no ambiente!")
# ---------------------------

# Carrega as variáveis do arquivo .env
load_dotenv()

# Cria a instância da aplicação (o objeto que representa o site)
app = Flask(__name__)

# --- SEGURANÇA ---
# Tenta pegar do Render (os.environ). Se não achar, usa a string fixa (para rodar no PC).
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# --- BANCO DE DADOS ---
database_url = os.environ.get('DATABASE_URL')

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa as extensões
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login' # Se alguém tentar acessar página restrita, vem pra cá

# Importa as rotas (atenção: deve ser importado DEPOIS de criar o app para evitar erro circular)
from app import routes, models