from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from apimercadopago import gerar_link_pagamento
import sqlite3
import os

# ------------------------------------------------
# DEFINIÇÃO DA APLICAÇÃO (Fica sempre no topo!)
# ------------------------------------------------
app = Flask(__name__)
app.secret_key = '1717'

# Configuração para upload
UPLOAD_FOLDER = 'static/img/products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ------------------------------------------------
# FUNÇÕES DE CONEXÃO E CRIAÇÃO DE TABELAS (DEFINIÇÃO)
# ------------------------------------------------

def get_user_db_connection():
    conn = sqlite3.connect('usuarios.db')
    conn.row_factory = sqlite3.Row
    return conn

def criar_usuario_admin():
    conn = get_user_db_connection()
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        conn.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (
            "admin",
            "admin@example.com",
            generate_password_hash("10203040", method='pbkdf2:sha256'),
        ))
        conn.commit()
        print("Usuário 'admin' criado com sucesso.")
    else:
        print("Usuário 'admin' já existe.")
    conn.close()

def criar_usuario_teste():
    conn = get_user_db_connection()
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", ("Teste_Teste",))
    if cursor.fetchone() is None:
        conn.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (
            "Teste_Teste",
            "teste@teste.com",
            generate_password_hash("123456", method='pbkdf2:sha256'),
        ))
        conn.commit()
        print("Usuário 'teste' criado com sucesso.")
    else:
        print("Usuário 'teste' já existe.")
    conn.close()

def create_user_table():
    conn = get_user_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

    criar_usuario_admin()
    criar_usuario_teste()

def create_historico_table():
    conn = get_user_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS historico_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_total REAL NOT NULL,
            payment_id TEXT,
            preference_id TEXT,
            status_pagamento TEXT,
            imagem TEXT,
            data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_loja_db_connection():
    conn = sqlite3.connect('loja.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_loja_table():
    conn = sqlite3.connect('loja.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            descricao TEXT NOT NULL,
            imagem TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def get_pagamentos_db_connection():
    conn = sqlite3.connect('pagamentos.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_pagamentos_table():
    conn = sqlite3.connect('pagamentos.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS payment (
            payment_id INTEGER PRIMARY KEY,
            status TEXT NOT NULL,
            payment_type TEXT NOT NULL,
            preference_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def inserir_produtos():
    produtos = {
        1: {"nome": "Shell Helix HX8 5W30", "preco": 120.00, "descricao": "Terço com pedras naturais e detalhes únicos.", "imagem": "img/products/terco01.png"},
        2: {"nome": "Lubrax Top Turbo 15W40", "preco": 150.00, "descricao": "Terço com cristais transparentes, trazendo um brilho especial.", "imagem": "img/products/terco02.png"},
        3: {"nome": "Mobil Super Dexos 1 5W30", "preco": 220.00, "descricao": "Terço com Quartzo transparentes, trazendo um brilho especial.", "imagem": "img/products/terco03.png"},
        4: {"nome": "Moura M60AD", "preco": 180.00, "descricao": "Terço feito com pérolas de alta qualidade, ideal para ocasiões especiais.", "imagem": "img/products/terco04.png"},
        5: {"nome": "Zetta Free Z2D", "preco": 90.00, "descricao": "Terço de madeira artesanal, com detalhes rústicos.", "imagem": "img/products/terco05.png"},
        6: {"nome": "Heliar AGM Start-Stop", "preco": 200.00, "descricao": "Terço de metal com acabamento elegante e durável.", "imagem": "img/products/terco06.png"},
        7: {"nome": "Continental PowerContact 2 185/65 R15", "preco": 70.00, "descricao": "Terço emborrachado, confortável para segurar e ideal para o dia a dia.", "imagem": "img/products/terco07.png"},
        8: {"nome": "Dunlop SP Touring 175/65 R14", "preco": 130.00, "descricao": "Terço feito com contas de vidro, dando um visual translúcido.", "imagem": "img/products/terco08.png"},
        9: {"nome": "Goodyear EfficientGrip SUV 225/55 R1", "preco": 170.00, "descricao": "Terço de porcelana delicada, perfeito para colecionadores.", "imagem": "img/products/terco09.png"},
        10: {"nome": "Cobreq N-208", "preco": 140.00, "descricao": "Terço com contas de pedra vulcânica, com textura única.", "imagem": "img/products/terco10.png"},
        11: {"nome": "Bosch BP976", "preco": 160.00, "descricao": "Terço de ágata natural, cada conta com suas variações de cor.", "imagem": "img/products/terco11.png"},
        12: {"nome": "TRW GDB1330", "preco": 95.00, "descricao": "Terço feito com contas de sândalo, com aroma natural.", "imagem": "img/products/terco12.png"},
        13: {"nome": "Fram CA4309", "preco": 125.00, "descricao": "Terço de hematita, trazendo um visual metálico escuro.", "imagem": "img/products/terco13.png"},
        14: {"nome": "Mann C 35 154", "preco": 190.00, "descricao": "Terço feito com contas de jade, conhecido por suas propriedades espirituais.", "imagem": "img/products/terco14.png"},
        15: {"nome": "Tecfil ARL 19", "preco": 210.00, "descricao": "Terço de ametista, com belas pedras roxas, ideal para meditação.", "imagem": "img/products/terco15.png"}
    }

    conn = sqlite3.connect('loja.db')
    c = conn.cursor()

    for produto in produtos.values():
        c.execute('SELECT id FROM produtos WHERE nome = ?', (produto['nome'],))
        resultado = c.fetchone()

        if not resultado:
            c.execute('''
                INSERT INTO produtos (nome, preco, descricao, imagem)
                VALUES (?, ?, ?, ?)
            ''', (produto['nome'], produto['preco'], produto['descricao'], produto['imagem']))

    conn.commit()
    conn.close()

# ------------------------------------------------
# ROTAS (Sem alterações)
# ------------------------------------------------

@app.route('/user')
def user():
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar essa página.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_user_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    historico = conn.execute('''
        SELECT id, produto_nome, quantidade, preco_total, data_compra, payment_id, status_pagamento
        FROM historico_compras
        WHERE user_id = ?
        ORDER BY data_compra DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('user.html', user=user, historico=historico)

@app.route('/admin')
def admin():
    if session.get('username') == 'admin':
        conn = get_loja_db_connection()
        produtos = conn.execute('SELECT * FROM produtos').fetchall()
        conn.close()
        return render_template('admin.html', produtos=produtos)
    else:
        flash("Acesso negado. Faça login como administrador para acessar.")
        return redirect(url_for('login'))

@app.route('/productcontrol')
def product_control():
    if session.get('username') == 'admin':
        conn = get_loja_db_connection()
        produtos = conn.execute('SELECT * FROM produtos').fetchall()
        conn.close()
        return render_template('product_control.html', produtos=produtos)
    else:
        flash("Acesso negado. Faça login como administrador para acessar.")
        return redirect(url_for('login'))

@app.route('/usercontrol')
def user_control():
    if session.get('username') == 'admin':
        conn = get_user_db_connection()
        users = conn.execute('SELECT * FROM users').fetchall()
        conn.close()
        return render_template('user_control.html', users=users)
    else:
        flash("Acesso negado. Faça login como administrador para acessar.")
        return redirect(url_for('login'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('username') == 'admin':
        conn = get_user_db_connection()
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash('Usuário removido com sucesso!', 'success')
    else:
        flash('Acesso negado.', 'danger')
    return redirect(url_for('usercontrol'))

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('username') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('login'))

    conn = get_user_db_connection()

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if password:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            conn.execute('UPDATE users SET username = ?, email = ?, password = ? WHERE id = ?',
                         (username, email, hashed_password, user_id))
        else:
            conn.execute('UPDATE users SET username = ?, email = ? WHERE id = ?',
                         (username, email, user_id))

        conn.commit()
        conn.close()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('user_control'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_user_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Login realizado com sucesso!', 'success')
                if username == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('user'))

        flash('Credenciais inválidas. Tente novamente.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/')
def index():
    conn = sqlite3.connect('loja.db')
    c = conn.cursor()

    c.execute('SELECT id, nome, preco, imagem FROM produtos')
    produtos = c.fetchall()

    conn.close()

    return render_template('index.html', produtos=produtos)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Senhas não coincidem.')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            conn = get_user_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                           (username, email, hashed_password))
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso! Faça login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Este e-mail ou nome de usuário já está cadastrado. Tente usar outro.')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('user', None)

    flash('Você foi desconectado com sucesso.', 'success')

    return redirect(request.referrer or url_for('index'))

@app.route('/produto/<int:produto_id>')
def produto(produto_id):
    conn = sqlite3.connect('loja.db')
    conn.row_factory = sqlite3.Row

    c = conn.cursor()
    c.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,))
    produto = c.fetchone()

    conn.close()

    if produto is None:
        flash('Produto não encontrado!', 'danger')
        return redirect(url_for('index'))

    return render_template('produto.html', produto=produto)

@app.context_processor
def carrinho_context():
    carrinho = session.get('carrinho', [])
    quantidade_total = sum(item['quantidade'] for item in carrinho)
    return {'quantidade_total': quantidade_total}

@app.route('/carrinho', methods=['GET', 'POST'])
def carrinho():
    carrinho = session.get('carrinho', [])

    if not carrinho:
        return render_template(
            'carrinho.html',
            carrinho=[],
            subtotal=0,
            link_pagamento=None
        )

    subtotal = sum(item['quantidade'] * item['preco'] for item in carrinho)

    itens_mp = [
        {
            "id": str(item['id']),
            "title": item['nome'],
            "quantity": item['quantidade'],
            "currency_id": "BRL",
            "unit_price": float(item['preco'])
        }
        for item in carrinho
    ]

    link_iniciar_pagamento = gerar_link_pagamento(itens_mp)

    return render_template(
        'carrinho.html',
        carrinho=carrinho,
        subtotal=subtotal,
        link_pagamento=link_iniciar_pagamento
    )

@app.route('/repetir_compra', methods=['POST'])
def repetir_compra():
    produto_id = request.form.get('id')
    produto_nome = request.form.get('produto_nome')
    quantidade = int(request.form.get('quantidade', 1))
    preco = float(request.form.get('preco', 0.0))

    if 'carrinho' not in session:
        session['carrinho'] = []

    carrinho = session['carrinho']

    produto_existente = next((item for item in carrinho if item['id'] == produto_id), None)
    if produto_existente:
        produto_existente['quantidade'] += quantidade
    else:
        carrinho.append({
            "id": produto_id,
            "nome": produto_nome,
            "quantidade": quantidade,
            "preco": preco,
        })

    session['carrinho'] = carrinho
    flash(f"O produto {produto_nome} foi adicionado ao carrinho.", "success")
    return redirect(url_for('carrinho'))

@app.route('/checkout')
def checkout():
    carrinho = session.get('carrinho', [])
    if not carrinho:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for('carrinho'))

    user_id = session.get('user_id')
    if not user_id:
        flash("Você precisa estar logado para finalizar a compra.", "warning")
        return redirect(url_for('login'))

    try:
        # Gerar link de pagamento
        link_pagamento = gerar_link_pagamento(carrinho)
        return redirect(link_pagamento)

    except KeyError as e:
        flash("Ocorreu um erro ao gerar o link de pagamento. Por favor, tente novamente.", "danger")
        return redirect(url_for('carrinho'))

    except Exception as e:
        flash("Erro inesperado. Tente novamente.", "danger")
        return redirect(url_for('carrinho'))

@app.route('/compracerta')
def compracerta():
    try:
        preference_id = request.args.get('preference_id')
        payment_status = request.args.get('collection_status')
        payment_id = request.args.get('payment_id')
        user_id = session.get('user_id')

        if payment_status != 'approved':
            flash("Pagamento não aprovado. Entre em contato com o suporte.", "warning")
            return redirect(url_for('carrinho'))

        carrinho = session.get('carrinho', [])
        conn = get_user_db_connection()

        for item in carrinho:
            conn.execute('''
                INSERT INTO historico_compras (user_id, produto_nome, quantidade, preco_total, payment_id, preference_id, status_pagamento, imagem)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                item['nome'],
                item['quantidade'],
                item['quantidade'] * item['preco'],
                payment_id,
                preference_id,
                payment_status,
                item['imagem']
            ))
        conn.commit()
        conn.close()

        session.pop('carrinho', None)
        flash("Compra realizada com sucesso! Histórico atualizado.", "success")
        return redirect(url_for('user'))

    except Exception as e:
        flash("Erro ao processar a compra. Tente novamente ou entre em contato com o suporte.", "danger")
        return redirect(url_for('carrinho'))

def get_produto_by_id(produto_id):
    conn = get_loja_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    conn.close()
    return produto


@app.route('/adicionar_ao_carrinho', methods=['POST'])
def adicionar_ao_carrinho():
    try:
        produto_id = int(request.form.get('produto_id'))
        quantidade = int(request.form.get('quantidade', 1))

        if 'carrinho' not in session:
            session['carrinho'] = []

        carrinho = session['carrinho']

        produto_existente = next((item for item in carrinho if item['id'] == produto_id), None)
        if produto_existente:
            produto_existente['quantidade'] += quantidade
        else:
            produto = get_produto_by_id(produto_id)

            if produto is None:
                return jsonify({'success': False, 'message': 'Produto não encontrado.'}), 404

            produto_carrinho = {
                'id': produto['id'],
                'nome': produto['nome'],
                'preco': produto['preco'],
                'imagem': produto['imagem'],
                'quantidade': quantidade
            }

            carrinho.append(produto_carrinho)

        session['carrinho'] = carrinho
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ocorreu um erro: {str(e)}'}), 500

@app.route('/remover_do_carrinho/<int:produto_id>', methods=['POST'])
def remover_do_carrinho(produto_id):
    carrinho = session.get('carrinho', [])
    carrinho = [item for item in carrinho if item['id'] != produto_id]
    session['carrinho'] = carrinho
    return redirect(url_for('carrinho'))

@app.route('/atualizar_quantidade/<int:produto_id>', methods=['POST'])
def atualizar_quantidade(produto_id):
    acao = request.form.get('acao')
    carrinho = session.get('carrinho', [])

    for item in carrinho:
        if item['id'] == produto_id:
            if acao == 'incrementar':
                item['quantidade'] += 1
            elif acao == 'decrementar':
                if item['quantidade'] > 1:
                    item['quantidade'] -= 1
                else:
                    carrinho.remove(item)
            break

    session['carrinho'] = carrinho
    return redirect(url_for('carrinho'))

@app.route('/adicionar_produto', methods=['POST'])
def adicionar_produto():
    if session.get('username') != 'admin':
        flash("Acesso negado. Somente administradores podem adicionar produtos.")
        return redirect(url_for('login'))

    nome = request.form['nome']
    preco = request.form['preco']
    descricao = request.form['descricao']

    imagem_file = request.files.get('imagem')
    if imagem_file and imagem_file.filename:
        filename = secure_filename(imagem_file.filename)
        imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagem_file.save(imagem_path)
        imagem = f'img/products/{filename}'
    else:
        imagem = None

    conn = get_loja_db_connection()
    conn.execute('INSERT INTO produtos (nome, preco, descricao, imagem) VALUES (?, ?, ?, ?)',
                 (nome, preco, descricao, imagem))
    conn.commit()
    conn.close()

    flash('Produto adicionado com sucesso!', 'success')
    return redirect(url_for('admin'))

@app.route('/editar_produto/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    if session.get('username') != 'admin':
        flash("Acesso negado. Somente administradores podem editar produtos.")
        return redirect(url_for('login'))

    conn = get_loja_db_connection()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        
        # 1. PEGA O PATH DA IMAGEM ATUAL (do campo hidden)
        imagem_atual = request.form['imagem_existente']
        imagem = imagem_atual # Inicializa com a imagem atual

        # 2. VERIFICA SE UM NOVO ARQUIVO FOI ENVIADO
        imagem_file = request.files.get('imagem_file')
        
        if imagem_file and imagem_file.filename:
            # Novo arquivo encontrado: salva e atualiza o path
            filename = secure_filename(imagem_file.filename)
            imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagem_file.save(imagem_path)
            
            # Atualiza a variável 'imagem' com o novo caminho relativo
            imagem = f'img/products/{filename}'

        # 3. EXECUTA O UPDATE NO BANCO DE DADOS
        conn.execute('UPDATE produtos SET nome = ?, preco = ?, descricao = ?, imagem = ? WHERE id = ?',
                     (nome, preco, descricao, imagem, produto_id))
        conn.commit()
        conn.close() # Fecha a conexão após o commit
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin'))

    # Método GET (Exibe o formulário)
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    conn.close()

    return render_template('editar_produto.html', produto=produto)

# NOVO: Rota para exibir a lista de produtos editáveis
@app.route('/editar_varios_produtos', methods=['GET'])
def editar_varios_produtos():
    if session.get('username') != 'admin':
        flash("Acesso negado. Faça login como administrador para acessar.")
        return redirect(url_for('login'))
    
    conn = get_loja_db_connection()
    # Carrega todos os produtos ordenados por ID
    produtos = conn.execute('SELECT * FROM produtos ORDER BY id').fetchall()
    conn.close()
    
    return render_template('editar_varios_produtos.html', produtos=produtos)

# NOVO: Rota para salvar todas as alterações
@app.route('/salvar_varios_produtos', methods=['POST'])
def salvar_varios_produtos():
    if session.get('username') != 'admin':
        flash("Acesso negado.")
        return redirect(url_for('login'))

    # Pega listas de todos os IDs e seus respectivos campos
    # Usamos getlist para capturar todos os valores de inputs com o mesmo 'name'
    ids = request.form.getlist('produto_id')
    nomes = request.form.getlist('nome')
    precos = request.form.getlist('preco')
    descricoes = request.form.getlist('descricao')
    
    conn = get_loja_db_connection()
    
    try:
        total_alteracoes = 0
        
        # Itera sobre os IDs e atualiza cada produto
        for i, produto_id_str in enumerate(ids):
            produto_id = int(produto_id_str)
            nome = nomes[i]
            preco = float(precos[i].replace(',', '.')) # Garante que aceita vírgula ou ponto
            descricao = descricoes[i]
            
            # Executa o UPDATE
            conn.execute('''
                UPDATE produtos 
                SET nome = ?, preco = ?, descricao = ? 
                WHERE id = ?
            ''', (nome, preco, descricao, produto_id))
            
            total_alteracoes += 1
            
        conn.commit()
        flash(f'{total_alteracoes} produtos atualizados com sucesso!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao salvar alterações: {e}', 'danger')
        
    finally:
        conn.close()
        
    return redirect(url_for('product_control'))

@app.route('/remover_produto/<int:produto_id>')
def remover_produto(produto_id):
    if session.get('username') != 'admin':
        flash("Acesso negado. Somente administradores podem remover produtos.")
        return redirect(url_for('login'))

    conn = get_loja_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
    conn.commit()
    conn.close()

    flash('Produto removido com sucesso!', 'success')
    return redirect(url_for('admin'))

# ------------------------------------------------
# BLOCO DE EXECUÇÃO (Para Rodar Localmente)
# ------------------------------------------------
if __name__ == '__main__':
    print("Iniciando a criação e preenchimento dos bancos de dados...")
    
    # Executa a lógica de criação e preenchimento de DBs
    create_user_table()
    create_historico_table()
    create_loja_table()
    create_pagamentos_table()
    inserir_produtos()
    
    # Roda a aplicação Flask
    app.run(debug=True)