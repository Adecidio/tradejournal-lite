import os
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, login
from app.models import User
from app.services import processar_relatorio

# Configuração> Onde salvar o arquivo?
# Pega o diretório atual do projeto + app + uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'uploads')

# Garante que a paste existe (se não, cria)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ROTA TEMPORÁRIA DE SETUP ---
@app.route('/criar-tabelas-agora')
def criar_tabelas():
    try:
        db.create_all()
        return "<h1>Sucesso! Tabelas criadas no PostgreSQL.</h1>"
    except Exception as e:
        return f"<h1>Erro:</h1> <p>{str(e)}</p>"

# --- Função Auxiliar para o Flask-Login saber quem é quem ---
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))  # Busca o usuário pelo ID no banco

# --- Rota Principal (Home) ---
@app.route('/', methods=['GET', 'POST']) # POST para o envio de dados
@app.route('/index', methods=['GET', 'POST'])
@login_required # Rota de Segurança! Só entra logado.

def index():
    # Se o usuário apertou o botão "Analisar" (fez um POST)
    if request.method == 'POST':
        # Verifica se o arquivo veio no formulário
        if 'file' not in request.files:
            return "Nenhum arquivo enviado!"
        
        file = request.files['file']

        # Se o usuário enviou um arquivo vazio
        if file.filename == '':
            return "Nenhum arquivo selecionado!"
        
        if file:
            # 1. Salva o arquivo na pasta uploads
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            resultado = processar_relatorio(filepath)

            # 2. Verifica se deu erro
            if "erro" in resultado:
                return f"<h3 style='color:red'>Erro: {resultado['erro']}</h3>"

            # 3. Mostra o Dashboard enviando os dados (resultado) para o HTML
            return render_template('dashboard.html', dados=resultado)

    return render_template('index.html')

# --- Rota de Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Se já está logado, manda para home

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Busca usuário no banco
        user = User.query.filter_by(username=username).first()

        # Verifica se usuário exite E se a senha bate com o hash
        if user is None or not check_password_hash(user.password_hash, password):
            flash('Nome do usuário ou senha inválidos', 'danger')  # Mensagem de erro
            return redirect(url_for('login'))

        # Se deu tudo certo:
        login_user(user)
        return redirect(url_for('index'))

    return render_template('login.html')

# --- Rota de Logout ---
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Rota de Registro (Criar Conta) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Verifica se já existe
        if User.query.filter_by(username=username).first():
            flash('Esse nome de usuário já existe.', 'warning')
            return redirect(url_for('register'))

        # Cria o novo usuário
        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)  # Gera a cifra da senha

        # Salva no banco (Commit)
        db.session.add(user)
        db.session.commit()

        flash('Parabéns! Você foi registrado. Faça login agora.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# --- Rota da Página de Preços ---
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# --- Rota que SIMULA o Pagamento ---
@app.route('/fake_checkout')
@login_required
def fake_checkout():
    """
    Simula o fluxo de pagamento.
    """
    # 1. Simula o processamento do cartão... (fingindo demora)
    # ... processando ...

    # 2. Pagamento Aprovado! Vamos promover o usuário.
    current_user.is_premium = True

    # 3. Salva a alteração no banco de dados
    db.session.commit()

    # 4. Feedback para o usuário
    flash('Pagamento confirmado! Bem-vindo ao time Premium 🚀', 'success')
    return redirect(url_for('index'))
