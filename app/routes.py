import os
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, login
from app.models import User, Trade
from app.services import salvar_trades_do_excel, gerar_dados_dashboard

# Configuração> Onde salvar o arquivo?
# Pega o diretório atual do projeto + app + uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'uploads')

# Garante que a paste existe (se não, cria)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ROTA TEMPORÁRIA ---
@app.route('/reset-banco-completo')
def reset_banco():
    try:
        db.drop_all()
        db.create_all()
        return "<h1>Sucesso!</h1> <p>Banco resetado. Tabela antiga 'user' removida e tabela nova 'users' criada.</p>"
    except Exception as e:
        return f"<h1>Erro:</h1> <p>{str(e)}</p>"
    
# --- Função Auxiliar para o Flask-Login saber quem é quem ---
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))  # Busca o usuário pelo ID no banco

# --- Rota Principal (Home) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # 1. Se for Visitante -> Mostra Landing Page
    if not current_user.is_authenticated:
        return render_template('landing.html')
    
    # 2. Se for Usuário Logado...

    # Lógica de Upload (POST)
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # CHAVA O SERVIÇO DE SALVAR (Passando o usuário atual)
            resultado = salvar_trades_do_excel(filepath, current_user)

            if 'erro' in resultado:
                flash(f"Erro: {resultado['erro']}", 'danger')
            else:
                qtd = resultado['novos_trades']
                flash(f"Sucesso! {qtd} novos trades importados para o banco.", 'success')

            # Remove o arquivo temporário para não lotar o servidor
            if os.path.exists(filepath):
                os.remove(filepath)

            return redirect(url_for('index'))
    
    # LÓGICA DO GET (FILTROS) ---
    # Captura os parâmetros da URL (se existirem)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    # Passa as datas para a função (agora ela aceita esses argumentos)
    dados_dashboard = gerar_dados_dashboard(current_user, data_inicio, data_fim)

    return render_template('dashboard.html',
                           dados=dados_dashboard,
                           # Passamos as datas de volta para o HTML preencher os campos
                           filtro_inicio=data_inicio,
                           filtro_fim=data_fim)
    
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

@app.route('/limpar-dados', methods=['POST'])
@login_required
def limpar_dados():
    try:
        # Apaga TODOS os trades onde o user_id é igual ao do utilizador atual
        num_deleted = Trade.query.filter_by(user_id=current_user.id).delete()

        # IMPORTANTE: O commit para confirmar a exclusão!
        db.session.commit()

        flash(f'Histórico limpo! {num_deleted} operações forma removidas.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao limpar o histórico.', 'danger')
        print(f"Erro ao deletar: {e}")

    return redirect(url_for('index'))

@app.route('/virar-pro')
@login_required
def virar_pro():
    # Simula o pagamento aprovado
    current_user.plan_type = 'pro'
    db.session.commit()
    flash('Parabéns! Você agora é um usuário PRO 👑', 'success')
    return redirect(url_for('index'))

@app.route('/virar-free')
@login_required
def virar_free():
    # Simula o cancelamento ou expiração
    current_user.plan_type = 'free'
    db.session.commit()
    flash('Você voltou para o plano FREE.', 'info')
    return redirect(url_for('index'))

@app.route('/salvar-anotacao', methods=['POST'])
@login_required
def salvar_anotacao():
    trade_id = request.form.get('trade_id')
    nota = request.form.get('nota')

    # Busca o trade e garante que pertence ao usuário logado
    trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first()

    if trade:
        trade.user_note = nota
        db.session.commit()
        flash('Anotação salva com sucesso! 📝', 'success')
    else:
        flash('Erro ao salvar anotação.', 'danger')

    return redirect(url_for('index'))