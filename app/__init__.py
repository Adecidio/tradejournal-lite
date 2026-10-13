from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager
import resend
import os
from urllib.parse import urlsplit, parse_qsl, urlencode
from dotenv import load_dotenv



# Carrega as variáveis do arquivo .env
load_dotenv()
resend.api_key = os.getenv('RESEND_API_KEY')

# Cria a instância da aplicação (o objeto que representa o site)
app = Flask(__name__)

# --- SEGURANÇA ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'


# --- BANCO DE DADOS ---
database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    parsed = urlsplit(database_url)
    if parsed.scheme in {'postgresql', 'postgres'}:
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if 'sslmode' not in query and 'render.com' in parsed.netloc:
            query['sslmode'] = 'require'
        if query:
            database_url = parsed._replace(query=urlencode(query, doseq=True)).geturl()

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Inicializa as extensões
db = SQLAlchemy(app)
login = LoginManager(app)

# Importa os modelos antes de criar as tabelas para que o SQLAlchemy conheça todas as classes
from app import models

with app.app_context():
    db.create_all()
    
    # Garante que as colunas de recuperação existam mesmo se a tabela for antiga
    try:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code VARCHAR(6);'))
            conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code_expiration TIMESTAMP WITH TIME ZONE;'))
            conn.commit()
    except Exception as e:
        print("Aviso na atualização das colunas:", e)

# Importa as rotas (atenção: deve ser importado DEPOIS de criar o app para evitar erro circular)
from app import routes