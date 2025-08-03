from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from apimercadopago import gerar_link_pagamento
import sqlite3
import os

app = Flask(__name__)
app.secret_key = '1717'  # Necessária para usar sessions

# Configuração para upload
UPLOAD_FOLDER = 'static/img/products'  # Diretório onde as imagens serão armazenadas
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de tamanho (16 MB)

# Verifica se o banco de dados já existe, e se existir, apaga para recriar.
#if os.path.exists('database.db'):
#    os.remove('database.db')

#if os.path.exists('loja.db'):
#    os.remove('loja.db')

def get_user_db_connection():
    conn = sqlite3.connect('usuarios.db')
    conn.row_factory = sqlite3.Row
    return conn

def criar_usuario_admin():
    conn = get_user_db_connection()

    # Verifique se o usuário padrão já existe
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        # Cria o usuário padrão
        conn.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (
            "admin",  # Nome de usuário
            "admin@example.com",  # Email
            generate_password_hash("10203040", method='pbkdf2:sha256'),  # Senha hash
        ))
        conn.commit()
        print("Usuário 'admin' criado com sucesso.")
    else:
        print("Usuário 'admin' já existe.")
    
    conn.close()

def criar_usuario_teste():
    conn = get_user_db_connection()

    # Verifique se o usuário padrão já existe
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", ("Teste_Teste",))
    if cursor.fetchone() is None:
        # Cria o usuário padrão
        conn.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (
            "Teste_Teste",  # Nome de usuário
            "teste@teste.com",  # Email
            generate_password_hash("123456", method='pbkdf2:sha256'),  # Senha hash
        ))
        conn.commit()
        print("Usuário 'teste' criado com sucesso.")
    else:
        print("Usuário 'teste' já existe.")
    
    conn.close()

# Criação do banco de dados e a tabela de usuarios
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
create_user_table() # Chama a função para criar o banco e a tabela

def create_historico_table():
    conn = get_user_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS historico_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_total REAL NOT NULL,
            payment_id TEXT,                 -- ID do pagamento do Mercado Pago
            preference_id TEXT,              -- ID da preferência do Mercado Pago
            status_pagamento TEXT,           -- Status do pagamento (e.g., aprovado, pendente, recusado)
            imagem TEXT,                     -- Caminho da imagem do produto
            data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Chama a função para criar a tabela ao iniciar o aplicativo
create_historico_table()

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

def get_loja_db_connection():
    conn = sqlite3.connect('loja.db')
    conn.row_factory = sqlite3.Row  # Para retornar as linhas como dicionários
    return conn

# Criação do banco de dados e a tabela de produtos
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
create_loja_table() # Chama a função para criar o banco e a tabela

def get_pagamentos_db_connection():
    conn = sqlite3.connect('pagamentos.db')
    conn.row_factory = sqlite3.Row  # Para retornar as linhas como dicionários
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
create_pagamentos_table() # Chama a função para criar o banco e a tabela

# Rota para a página admin
@app.route('/admin')
def admin():
    if session.get('username') == 'admin':  # Verifica se o usuário na sessão é 'admin'
        conn = get_loja_db_connection()
        produtos = conn.execute('SELECT * FROM produtos').fetchall()  # Busca todos os produtos
        conn.close()
        return render_template('admin.html', produtos=produtos)  # Passa a lista de produtos para a página
    else:
        flash("Acesso negado. Faça login como administrador para acessar.")
        return redirect(url_for('login'))
    
@app.route('/productcontrol')
def product_control():
    if session.get('username') == 'admin':  # Verifica se o usuário na sessão é 'admin'
        conn = get_loja_db_connection()
        produtos = conn.execute('SELECT * FROM produtos').fetchall()  # Busca todos os produtos
        conn.close()
        return render_template('product_control.html', produtos=produtos)  # Passa a lista de produtos para a página
    else:
        flash("Acesso negado. Faça login como administrador para acessar.")
        return redirect(url_for('login'))

@app.route('/usercontrol')
def user_control():
    if session.get('username') == 'admin':  # Apenas o administrador pode acessar
        conn = get_user_db_connection()
        users = conn.execute('SELECT * FROM users').fetchall()  # Busca todos os usuários
        conn.close()
        return render_template('user_control.html', users=users)  # Passa os usuários para o template
    else:
        flash("Acesso negado. Faça login como administrador para acessar.")
        return redirect(url_for('login'))
    
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('username') == 'admin':  # Verifica se o usuário é admin
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
        print("Requisição POST recebida no login")

        # Obtenção dos dados do formulário
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Dados recebidos - Username: {username}, Password: [oculto]")

        # Busca o usuário no banco de dados
        conn = get_user_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        print(f"Resultado da consulta ao banco de dados: {user}")

        # Verifica se o usuário existe e se a senha está correta
        if user:
            print("Usuário encontrado, verificando senha...")
            if check_password_hash(user['password'], password):  # Usando `user['password']` para pegar o campo da senha
                session['user_id'] = user['id']  # Salvando o ID do usuário na sessão
                session['username'] = user['username']  # Salvando o nome de usuário na sessão
                print(f"Login bem-sucedido para o usuário: {username}")
                flash('Login realizado com sucesso!', 'success')
                if username == 'admin':  # Verifica se o nome de usuário é 'admin'
                    return redirect(url_for('admin'))  # Redireciona para a página de administração
                else:
                    return redirect(url_for('user'))  # Redirecionar para a página principal
            # Verifica se o usuário é o admin e redireciona para a página de administração
            
            else:
                print("Senha incorreta")
        else:
            print("Usuário não encontrado")
        
        
        # Caso as credenciais estejam incorretas
        flash('Credenciais inválidas. Tente novamente.', 'danger')
        return redirect(url_for('login'))

    # Se o método for GET, renderiza a página de login
    print("Método GET recebido, exibindo a página de login")
    return render_template('login.html')

@app.route('/')
def index():
    conn = sqlite3.connect('loja.db')
    c = conn.cursor()
    
    # Buscar todos os produtos no banco de dados
    c.execute('SELECT id, nome, preco, imagem FROM produtos')
    produtos = c.fetchall()
    
    conn.close()

    # Renderizar a página com os produtos
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
    # Limpa a sessão do usuário
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('user', None)
    
    # Adiciona uma mensagem flash
    flash('Você foi desconectado com sucesso.', 'success')
    
    # Redireciona de volta para a página de onde veio o usuário (request.referrer)
    return redirect(request.referrer or url_for('index'))  # Redireciona para a página inicial caso não haja referrer

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
        # Verifica se o produto já existe no banco
        c.execute('SELECT id FROM produtos WHERE nome = ?', (produto['nome'],))
        resultado = c.fetchone()

        # Se não existir, insere o produto
        if not resultado:
            c.execute('''
                INSERT INTO produtos (nome, preco, descricao, imagem)
                VALUES (?, ?, ?, ?)
            ''', (produto['nome'], produto['preco'], produto['descricao'], produto['imagem']))

    conn.commit()
    conn.close()
# Chama a função para inserir os produtos
inserir_produtos()

@app.route('/produto/<int:produto_id>')
def produto(produto_id):
    # Conectar ao banco de dados e configurar o retorno como dicionário
    conn = sqlite3.connect('loja.db')
    conn.row_factory = sqlite3.Row  # Isso faz com que o SQLite retorne dicionários
    
    c = conn.cursor()

    # Consultar o produto com o id fornecido
    c.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,))
    produto = c.fetchone()  # Obtemos um único produto (dicionário agora)

    conn.close()

    # Se o produto não for encontrado, redireciona para a página principal ou exibe uma mensagem
    if produto is None:
        flash('Produto não encontrado!', 'danger')
        return redirect(url_for('index'))

    # Passa as informações do produto para o template 'produto.html'
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
        # Redireciona para a página inicial ou exibe uma mensagem no carrinho vazio
        return render_template(
            'carrinho.html',
            carrinho=[],
            subtotal=0,
            link_pagamento=None
        )

    subtotal = sum(item['quantidade'] * item['preco'] for item in carrinho)

    # Prepara os itens no formato necessário para o Mercado Pago
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

    # Gera o link de pagamento somente se houver itens no carrinho
    link_iniciar_pagamento = gerar_link_pagamento(itens_mp)

    return render_template(
        'carrinho.html',
        carrinho=carrinho,
        subtotal=subtotal,
        link_pagamento=link_iniciar_pagamento
    )

@app.route('/repetir_compra', methods=['POST'])
def repetir_compra():
    produto_id = request.form.get('id')  # Captura o ID do produto
    produto_nome = request.form.get('produto_nome')
    quantidade = int(request.form.get('quantidade', 1))
    preco = float(request.form.get('preco', 0.0))

    if 'carrinho' not in session:
        session['carrinho'] = []

    carrinho = session['carrinho']

    # Verifica se o produto já está no carrinho
    produto_existente = next((item for item in carrinho if item['id'] == produto_id), None)
    if produto_existente:
        produto_existente['quantidade'] += quantidade
    else:
        carrinho.append({
            "id": produto_id,  # Certifique-se de que 'id' está sendo passado
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
        # Salvar os itens do carrinho no histórico de compras
        conn = get_user_db_connection()
        for item in carrinho:
            conn.execute('''
                INSERT INTO historico_compras (user_id, produto_nome, quantidade, preco_total, imagem)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, item['nome'], item['quantidade'], item['quantidade'] * item['preco'], item['imagem']))
        conn.commit()
        conn.close()

        # Gerar link de pagamento
        link_pagamento = gerar_link_pagamento(carrinho)
        print(f"Link de pagamento gerado: {link_pagamento}")  # Debug para terminal
        return redirect(link_pagamento)

    except KeyError as e:
        print("Erro ao acessar init_point:", str(e))
        flash("Ocorreu um erro ao gerar o link de pagamento. Por favor, tente novamente.", "danger")
        return redirect(url_for('carrinho'))

    except Exception as e:
        print("Erro geral no checkout:", str(e))
        flash("Erro inesperado. Tente novamente.", "danger")
        return redirect(url_for('carrinho'))
    
@app.route('/compracerta')
def compracerta():
    try:
        # Parâmetros enviados pelo Mercado Pago
        preference_id = request.args.get('preference_id')
        payment_status = request.args.get('collection_status')
        payment_id = request.args.get('payment_id')
        user_id = session.get('user_id')

        print("payment_id recebido:", payment_id)  # Debug para verificar

        if payment_status != 'approved':
            flash("Pagamento não aprovado. Entre em contato com o suporte.", "warning")
            return redirect(url_for('carrinho'))

        # Salvar histórico da compra no banco de dados
        carrinho = session.get('carrinho', [])
        conn = get_user_db_connection()

        for item in carrinho:
            print(f"Salvando no banco: {item['nome']}, {item['imagem']}, {payment_id}, {preference_id}, {payment_status}")  # Debug

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
                item['imagem']  # Adiciona o caminho da imagem
            ))
        conn.commit()
        conn.close()

        session.pop('carrinho', None)
        flash("Compra realizada com sucesso! Histórico atualizado.", "success")
        return redirect(url_for('user'))

    except Exception as e:
        print("Erro ao processar a compra:", str(e))
        flash("Erro ao processar a compra. Tente novamente ou entre em contato com o suporte.", "danger")
        return redirect(url_for('carrinho'))

# Função para buscar o produto no banco de dados
def get_produto_by_id(produto_id):
    conn = get_loja_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    conn.close()
    return produto


@app.route('/adicionar_ao_carrinho', methods=['POST'])
def adicionar_ao_carrinho():
    try:
        # Debugging prints para identificar problemas
        print("Tentando adicionar produto ao carrinho...")

        produto_id = int(request.form.get('produto_id'))
        quantidade = int(request.form.get('quantidade', 1))

        print(f"Produto ID: {produto_id}, Quantidade: {quantidade}")

        # Se o carrinho não existir na sessão, cria um novo carrinho
        if 'carrinho' not in session:
            session['carrinho'] = []

        carrinho = session['carrinho']

        # Verifica se o produto já está no carrinho
        produto_existente = next((item for item in carrinho if item['id'] == produto_id), None)
        if produto_existente:
            produto_existente['quantidade'] += quantidade
            print(f"Produto já está no carrinho. Nova quantidade: {produto_existente['quantidade']}")
        else:
            # Busca o produto no banco de dados
            produto = get_produto_by_id(produto_id)

            # Se o produto não for encontrado, retorna um erro
            if produto is None:
                print("Erro: Produto não encontrado")
                return jsonify({'success': False, 'message': 'Produto não encontrado.'}), 404

            # Cria o dicionário do produto para adicionar ao carrinho
            produto_carrinho = {
                'id': produto['id'],
                'nome': produto['nome'],
                'preco': produto['preco'],
                'imagem': produto['imagem'],
                'quantidade': quantidade
            }

            # Adiciona o produto ao carrinho
            carrinho.append(produto_carrinho)
            print(f"Produto adicionado ao carrinho: {produto_carrinho}")

        # Atualiza o carrinho na sessão
        session['carrinho'] = carrinho
        print("Produto adicionado com sucesso ao carrinho!")
        return jsonify({'success': True})

    except Exception as e:
        print(f"Ocorreu um erro ao adicionar ao carrinho: {e}")
        return jsonify({'success': False, 'message': f'Ocorreu um erro: {str(e)}'}), 500

@app.route('/remover_do_carrinho/<int:produto_id>', methods=['POST'])
def remover_do_carrinho(produto_id):
    carrinho = session.get('carrinho', [])
    # Filtra o carrinho para remover o produto correspondente ao produto_id
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
                    # Remover o item se a quantidade for 1 e a ação for decrementar
                    carrinho.remove(item)
            break

    session['carrinho'] = carrinho
    return redirect(url_for('carrinho'))

# Rota para adicionar um novo produto
@app.route('/adicionar_produto', methods=['POST'])
def adicionar_produto():
    if session.get('username') != 'admin':  # Verifica se o usuário é admin
        flash("Acesso negado. Somente administradores podem adicionar produtos.")
        return redirect(url_for('login'))

    nome = request.form['nome']
    preco = request.form['preco']
    descricao = request.form['descricao']

    # Trata o upload de imagem
    imagem_file = request.files.get('imagem')  # Usa get() para evitar erros se o campo estiver vazio
    if imagem_file and imagem_file.filename:
        # Garante que o nome do arquivo é seguro
        filename = secure_filename(imagem_file.filename)
        imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # Salva o arquivo no diretório
        imagem_file.save(imagem_path)
        # Salva apenas o caminho relativo no banco de dados
        imagem = f'img/products/{filename}'
    else:
        imagem = None  # Ou defina um valor padrão, como 'uploads/default.jpg'

    # Conecta ao banco e salva os dados
    conn = get_loja_db_connection()
    conn.execute('INSERT INTO produtos (nome, preco, descricao, imagem) VALUES (?, ?, ?, ?)',
                 (nome, preco, descricao, imagem))
    conn.commit()
    conn.close()

    flash('Produto adicionado com sucesso!', 'success')
    return redirect(url_for('admin'))  # Redireciona para a página de administração

# Rota para editar um produto
@app.route('/editar_produto/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    if session.get('username') != 'admin':  # Verifica se o usuário é admin
        flash("Acesso negado. Somente administradores podem editar produtos.")
        return redirect(url_for('login'))

    conn = get_loja_db_connection()
    
    if request.method == 'POST':  # Quando o formulário for enviado (método POST)
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        imagem = request.form['imagem']

        conn.execute('UPDATE produtos SET nome = ?, preco = ?, descricao = ?, imagem = ? WHERE id = ?',
                     (nome, preco, descricao, imagem, produto_id))
        conn.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin'))  # Redireciona de volta para a página de administração

    # Quando o formulário for exibido (método GET)
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    conn.close()

    return render_template('editar_produto.html', produto=produto)  # Exibe o formulário de edição

# Rota para remover um produto
@app.route('/remover_produto/<int:produto_id>')
def remover_produto(produto_id):
    if session.get('username') != 'admin':  # Verifica se o usuário é admin
        flash("Acesso negado. Somente administradores podem remover produtos.")
        return redirect(url_for('login'))

    conn = get_loja_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
    conn.commit()
    conn.close()

    flash('Produto removido com sucesso!', 'success')
    return redirect(url_for('admin'))  # Redireciona de volta para a página de administração

if __name__ == '__main__':
    app.run(debug=True)
