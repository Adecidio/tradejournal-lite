from app import db, login
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# UserMixin dá superpoderes à classe (já traz métodos com is_authenticated)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # As colunas da tabela no banco de dados
    id = db.Column(db.Integer, primary_key=True) # Identidade única (CPF do banco)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False) # Nome de usuário
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)  #E-mail único
    password_hash = db.Column(db.String(256))  # Senha (nunca salvamos texto puro, salvamos hash!)
    plan_type = db.Column(db.String(20), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # RELACIONAMENTO: Um usuário tem MUITOS trades
    trades = db.relationship('Trade', backref='owner', lazy=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} - Plano: {self.plan_type}>'
    
# --- TABELA DE TRADES ---
class Trade(db.Model):
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)

    
    # Dados do Excel
    ticket = db.Column(db.String(32), index=True)
    symbol = db.Column(db.String(20))
    type = db.Column(db.String(20))
    volume = db.Column(db.Float)

    open_time = db.Column(db.DateTime)  # Horário Abertura
    close_time = db.Column(db.DateTime) # Horário Fechamento

    open_price = db.Column(db.Float)
    close_price = db.Column(db.Float)

    sl = db.Column(db.Float)
    tp = db.Column(db.Float)
    
    commission = db.Column(db.Float, default=0.0)
    swap = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float, default=0.0)

    net_result = db.Column(db.Float, default=0.0)
    # Text permite textos longos (anotações detalhadas)
    user_note = db.Column(db.Text, nullable=True)

    # Chave Estrangeira: Este trade pertence a qual usuário?
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Resultado calculado (Profit + Swap + Commission)
    def __repr__(self):
        return f'<Trade {self.ticket} do User {self.user_id}>'
    
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))
