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

def create_and_populate_tables(conn):
    """
    Cria as tabelas do sistema e popula com dados iniciais se estiverem vazias.
    Utiliza nomes de coluna curtos: codigo, preco, quantidade.
    """
    if conn is None:
        return

    cursor = conn.cursor()

    # 1. Tabela Produtos (VOLTANDO AOS NOMES DE COLUNA CURTOS: codigo, preco, quantidade)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,             -- Nome Curto
            nome TEXT NOT NULL,
            preco REAL NOT NULL,                    -- Nome Curto
            quantidade REAL NOT NULL DEFAULT 0,     -- Nome Curto
            tipo_medicao TEXT NOT NULL DEFAULT 'Unidade', 
            categoria TEXT NOT NULL,                -- Necessário para o insert
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

    # 3. Tabela Vendas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Vendas (
            venda_id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            total_venda REAL NOT NULL,
            valor_recebido REAL,
            troco REAL,
            vendedor_nome TEXT,
            id_funcionario INTEGER,
            FOREIGN KEY (id_funcionario) REFERENCES Funcionarios(id)
        )
    """)
    
    # 4. Tabela ItensVenda (FOREIGN KEY CORRIGIDA para Produtos(codigo))
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ItensVenda (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_codigo TEXT,
            nome_produto TEXT,
            quantidade REAL NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (venda_id) REFERENCES Vendas(venda_id),
            FOREIGN KEY (produto_codigo) REFERENCES Produtos(codigo) -- CORRIGIDO PARA codigo
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
                codigo, nome, preco, quantidade, tipo_medicao, categoria -- Nomes curtos
            ) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, produtos_iniciais)
        print("LOG: Produtos iniciais populados.")

    # Popula Administrador Inicial (Se não houver nenhum funcionário)
    cursor.execute("SELECT COUNT(*) FROM Funcionarios")
    if cursor.fetchone()[0] == 0:
        admin_data = ('Admin Master', 'admin', DEFAULT_ADMIN_PASSWORD_HASH, 'admin', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        cursor.execute("""
            INSERT INTO Funcionarios (nome, login, senha_hash, cargo, data_cadastro) 
            VALUES (?, ?, ?, ?, ?)
        """, admin_data)
        print("LOG: Administrador inicial (admin) criado.")

    conn.commit()

# --- FUNÇÕES DE DECREMENTO DE ESTOQUE E FINALIZAÇÃO DE VENDA ---

# ARQUIVO: core/database.py

import datetime as dt # Certifique-se de que o import está correto no topo do arquivo!

def finalizar_venda(db_conn, itens_venda, total, recebido, troco, id_funcionario, vendedor_nome): 
    """Registra a venda e os itens vendidos."""
    
    cursor = db_conn.cursor() 

    try:
        # 1. Inserir na tabela Vendas
        cursor.execute("""
            INSERT INTO Vendas (data_hora, total_venda, valor_recebido, troco, id_funcionario, vendedor_nome)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, recebido, troco, id_funcionario, vendedor_nome))
            
        venda_id = cursor.lastrowid 

        if venda_id is None:
            raise Exception("Falha ao obter o ID da venda recém-inserida.")

        # 3. Preparar dados para ItensVenda
        itens_venda_data = []
        
        # ⭐️ CORREÇÃO ESSENCIAL AQUI: Receber os 5 valores da tupla (inclui tipo_medicao) ⭐️
        for codigo, nome, quantidade, preco, tipo_medicao in itens_venda:
            
            # O tipo_medicao é ignorado aqui, pois a tabela ItensVenda só precisa dos 5 campos:
            # (venda_id, produto_codigo, nome_produto, quantidade, preco_unitario)
            itens_venda_data.append((venda_id, codigo, nome, quantidade, preco)) 
            
        # 4. Inserir na tabela ItensVenda
        # Esta instrução SQL ainda espera os 5 valores corretos (venda_id + 4 detalhes do produto)
        cursor.executemany("""
            INSERT INTO ItensVenda (venda_id, produto_codigo, nome_produto, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?, ?)
            """, itens_venda_data)
        
        # 5. Commit e retorno
        # O commit deve ser feito pelo gerenciador de transação, se o chamador (handle_finalize_sale) for o responsável.
        # Mas, se esta função é responsável pelo commit local, o código está correto:
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
    # ⭐️ Nomes Curto na Seleção ⭐️
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
        # Assumimos que o carrinho fornece 'codigo' que é o codigo do DB
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