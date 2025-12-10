import sqlite3
import os
from datetime import datetime
import datetime as dt # Alias para evitar conflito com datetime.now() em finalizar_venda

# Usaremos o hash SHA-256 da senha "admin" para compatibilidade com o LoginDialog
# Hash de "admin" (SHA-256): 8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
DEFAULT_ADMIN_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918" 

DB_NAME = 'pdv.db'
LOW_STOCK_THRESHOLD = 5 

# --- FUNÇÕES DE CONEXÃO E INICIALIZAÇÃO ---

def connect_db(parent=None):
    """Cria e retorna a conexão com o banco de dados SQLite."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA foreign_keys = ON") 
        return conn
    except sqlite3.Error as e:
        if parent and hasattr(parent, 'show_error_message'):
            parent.show_error_message("Erro de Conexão com o Banco de Dados", f"Falha ao conectar: {e}")
        return None 

def _check_and_update_tables(conn):
    """
    Função auxiliar para verificar e adicionar colunas de migração se necessário.
    Utilizada para garantir que as colunas de desconto/taxa e PagamentosVenda existam.
    """
    cursor = conn.cursor()
    
    # 1. Tabela PagamentosVenda (Garantir que exista)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PagamentosVenda (
            pagamento_id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            metodo TEXT NOT NULL, 
            valor REAL NOT NULL,
            FOREIGN KEY (venda_id) REFERENCES Vendas(venda_id) ON DELETE CASCADE
        )
    """)
    
    # 2. Verificar e adicionar colunas na tabela Vendas (para Desconto/Taxa)
    try:
        cursor.execute("SELECT valor_bruto FROM Vendas LIMIT 1")
    except sqlite3.OperationalError:
        print("LOG: Adicionando colunas de Desconto/Taxa à tabela Vendas.")
        cursor.execute("ALTER TABLE Vendas ADD COLUMN valor_bruto REAL")
        cursor.execute("ALTER TABLE Vendas ADD COLUMN desconto_aplicado REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE Vendas ADD COLUMN taxa_servico REAL DEFAULT 0.0")

    # 3. Verificar e adicionar colunas na tabela ItensVenda (para Desconto/Total Líquido)
    try:
        cursor.execute("SELECT desconto_item FROM ItensVenda LIMIT 1")
    except sqlite3.OperationalError:
        print("LOG: Adicionando colunas de Desconto/Total Líquido à tabela ItensVenda.")
        # Se a coluna 'desconto_item' não existir, cria as duas:
        cursor.execute("ALTER TABLE ItensVenda ADD COLUMN desconto_item REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE ItensVenda ADD COLUMN total_liquido_item REAL")
    
    conn.commit()


def create_and_populate_tables(conn):
    """
    Cria as tabelas do sistema, executa migrações necessárias e popula com dados iniciais.
    """
    if conn is None:
        return

    cursor = conn.cursor()

    # --- 0. Tenta aplicar migrações (garante tabelas PagamentosVenda e colunas de desconto) ---
    _check_and_update_tables(conn)

    # 1. Tabela Produtos
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL, 
            nome TEXT NOT NULL,
            preco REAL NOT NULL, 
            quantidade REAL NOT NULL DEFAULT 0, 
            tipo_medicao TEXT NOT NULL DEFAULT 'Unidade', 
            categoria TEXT NOT NULL, 
            ativo INTEGER NOT NULL DEFAULT 1 
        );
    """)
    
    # 2. Tabela Funcionarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            cargo TEXT NOT NULL,
            data_cadastro TEXT NOT NULL
        )
    """)

    # ⭐️ 3. Tabela CAIXA (NOVA IMPLEMENTAÇÃO) ⭐️
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_funcionario INTEGER NOT NULL,
            data_abertura TEXT NOT NULL,
            valor_abertura REAL NOT NULL,
            
            data_fechamento TEXT,             -- NULL se o caixa estiver Aberto
            valor_fechamento_declarado REAL,  -- NULL se o caixa estiver Aberto
            diferenca REAL,                   -- NULL se o caixa estiver Aberto
            
            status TEXT NOT NULL, -- 'Aberto', 'Fechado'
            
            FOREIGN KEY (id_funcionario) REFERENCES Funcionarios(id)
        )
    """)
    print("LOG: Tabela Caixa verificada/criada.")
    
    # 4. Tabela Vendas (Base)
    # A tabela Vendas só é criada se já não existir. As colunas de desconto são tratadas pelo _check_and_update_tables.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Vendas (
            venda_id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            total_venda REAL NOT NULL,
            valor_recebido REAL,
            troco REAL,
            vendedor_nome TEXT,
            id_funcionario INTEGER,
            -- Coluna para ligar a venda à sessão de caixa (NOVA FK)
            id_caixa INTEGER,
            FOREIGN KEY (id_funcionario) REFERENCES Funcionarios(id),
            FOREIGN KEY (id_caixa) REFERENCES Caixa(id)
        )
    """)
    
    # 5. Tabela ItensVenda
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ItensVenda (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_codigo TEXT,
            nome_produto TEXT,
            quantidade REAL NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (venda_id) REFERENCES Vendas(venda_id),
            FOREIGN KEY (produto_codigo) REFERENCES Produtos(codigo)
        )
    """)

    # --- Popula as tabelas APENAS se estiverem vazias ---
    
    # Popula Produtos
    cursor.execute("SELECT COUNT(*) FROM Produtos")
    if cursor.fetchone()[0] == 0:
        produtos_iniciais = [
            # (codigo, nome, preco, quantidade, tipo_medicao, categoria)
            ('001', 'Refrigerante Cola 2L', 7.50, 50.0, 'Unidade', 'Bebidas'),
            ('002', 'Pão Francês', 15.99, 10.0, 'Peso', 'Padaria'),
            ('003', 'Chocolate Barra 90g', 5.00, 100.0, 'Unidade', 'Doces'),
            ('004', 'Queijo Muçarela', 32.00, 5.0, 'Peso', 'Frios'),
            ('005', 'Água Mineral 500ml', 2.50, 200.0, 'Unidade', 'Bebidas'),
            ('006', 'Presunto Fatiado', 18.00, 8.0, 'Peso', 'Frios'),
            ('101', 'Bala de Goma', 0.10, 500.0, 'Unidade', 'Doces'),
        ]
        
        cursor.executemany("""
            INSERT INTO Produtos (
                codigo, nome, preco, quantidade, tipo_medicao, categoria
            ) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, produtos_iniciais)
        print("LOG: Produtos iniciais populados.")

    # Popula Administrador Inicial
    cursor.execute("SELECT COUNT(*) FROM Funcionarios")
    if cursor.fetchone()[0] == 0:
        admin_data = ('Admin Master', 'admin', DEFAULT_ADMIN_PASSWORD_HASH, 'admin', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        cursor.execute("""
            INSERT INTO Funcionarios (nome, login, senha_hash, cargo, data_cadastro) 
            VALUES (?, ?, ?, ?, ?)
        """, admin_data)
        print("LOG: Administrador inicial (admin) criado.")

    conn.commit()

# --- FUNÇÕES DE DECREMENTO DE ESTOQUE, FINALIZAÇÃO DE VENDA, etc. ---
# (Mantidas inalteradas, pois o fluxo atômico é tratado no VendasController)

# ARQUIVO: core/database.py

def finalizar_venda(db_conn, itens_venda, total, recebido, troco, id_funcionario, vendedor_nome): 
    # Esta função é a versão simplificada; a versão de transação (finalizar_venda_transacao) 
    # é que deve ser usada no controller, e nela precisaremos adicionar o id_caixa.
    # Esta função aqui provavelmente está obsoleta se o controller usar a transacao.
    # Por enquanto, mantemos, mas ela precisa ser atualizada para receber id_caixa se for utilizada.
    
    cursor = db_conn.cursor() 

    try:
        # 1. Inserir na tabela Vendas (MANTIDO INALTERADO POR ENQUANTO)
        cursor.execute("""
            INSERT INTO Vendas (data_hora, total_venda, valor_recebido, troco, id_funcionario, vendedor_nome)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, recebido, troco, id_funcionario, vendedor_nome))
            
        venda_id = cursor.lastrowid 

        if venda_id is None:
            raise Exception("Falha ao obter o ID da venda recém-inserida.")

        # 3. Preparar dados para ItensVenda
        itens_venda_data = []
        
        for codigo, nome, quantidade, preco, tipo_medicao in itens_venda:
            itens_venda_data.append((venda_id, codigo, nome, quantidade, preco)) 
            
        # 4. Inserir na tabela ItensVenda
        cursor.executemany("""
            INSERT INTO ItensVenda (venda_id, produto_codigo, nome_produto, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?, ?)
            """, itens_venda_data)
        
        db_conn.commit() 
        return venda_id 

    except Exception as e:
        db_conn.rollback()
        print(f"Erro ao finalizar venda: {e}")
        return None

def get_all_categories(conn):
    """Retorna uma lista de todas as categorias únicas de produtos."""
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categoria FROM Produtos ORDER BY categoria")
    return [row[0] for row in cursor.fetchall()]

def get_all_products(conn):
    """Retorna uma lista de todos os produtos com todas as colunas necessárias."""
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT codigo, nome, preco, quantidade, tipo_medicao, categoria 
        FROM Produtos 
        ORDER BY nome
    """)
    return cursor.fetchall()

def update_stock_after_sale(conn, cart_items):
    """
    Subtrai a quantidade vendida do estoque de cada produto.
    Assume que 'cart_items' são dicionários com 'codigo', 'quantidade', 'nome'.
    """
    
    cursor = conn.cursor()
    low_stock_alerts = []
    
    for item in cart_items:
        product_code = item['codigo'] 
        quantity_sold = item['quantidade']
        product_name = item['nome']
        
        # 1. Subtrai a quantidade vendida (Usando codigo)
        cursor.execute("""
            UPDATE Produtos 
            SET quantidade = quantidade - ? 
            WHERE codigo = ?; 
        """, (quantity_sold, product_code))
        
        # 2. Verifica o nível de estoque após a baixa
        cursor.execute("SELECT quantidade FROM Produtos WHERE codigo = ?", (product_code,))
        
        result = cursor.fetchone()
        if result is None:
            raise Exception(f"Produto não encontrado no DB durante a baixa de estoque: Código {product_code}")
            
        current_stock = result[0]
        
        if current_stock <= LOW_STOCK_THRESHOLD:
            low_stock_alerts.append(f"⚠️ {product_name}: Apenas {current_stock} em estoque!")
            
    return low_stock_alerts