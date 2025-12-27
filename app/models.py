from app import db
from flask_login import UserMixin
from datetime import datetime

# UserMixin dá superpoderes à classe (já traz métodos com is_authenticated)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # As colunas da tabela no banco de dados
    id = db.Column(db.Integer, primary_key=True) # Identidade única (CPF do banco)
    username = db.Column(db.String(64), index=True, unique=True) # Nome de usuário
    email = db.Column(db.String(120), index=True, unique=True)  #E-mail único
    password_hash = db.Column(db.String(128))  # Senha (nunca salvamos texto puro, salvamos hash!)

    # Campo para diferenciar usuário Grátis de Premium
    is_premium = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'