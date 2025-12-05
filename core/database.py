import sqlite3
import os

DB_NAME = 'pdv.db'

def connect_db(parent):
    """Cria e retorna a conexão com o banco de dados SQLite."""
    try:
        conn = sqlite3.connect(DB_NAME)
        # Habilita chaves estrangeiras
        conn.execute("PRAGMA foreign_keys = ON") 
        return conn
    except sqlite3.Error as e:
        # Assumindo que 'parent' tem um método para mostrar erro, como uma janela principal
        if parent and hasattr(parent, 'show_error_message'):
            parent.show_error_message("Erro de Conexão com o Banco de Dados", f"Falha ao conectar: {e}")
        return None

def create_and_populate_tables(conn):
    """
    Cria as tabelas do sistema (Produtos, Funcionarios, Vendas, ItensVenda) e 
    popula a tabela Produtos se estiver vazia.
    """
    if conn is None:
        return

    cursor = conn.cursor()

    # 1. Tabela Produtos (Atualizada com tipo_medicao e categoria)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Produtos (
            codigo TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            tipo_medicao TEXT NOT NULL, 
            categoria TEXT NOT NULL 
        )
    """)
    
    # ⭐️ CORREÇÃO: Nova Tabela Funcionarios (Com Login UNIQUE e senha_hash) ⭐️
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

    # 2. Tabela Vendas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Vendas (
            venda_id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            total_venda REAL NOT NULL,
            valor_recebido REAL,
            troco REAL
        )
    """)

    # 3. Tabela ItensVenda
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

    # --- Popula a tabela Produtos APENAS se estiver vazia ---
    cursor.execute("SELECT COUNT(*) FROM Produtos")
    if cursor.fetchone()[0] == 0:
        produtos_iniciais = [
            ('001', 'Refrigerante Cola 2L', 7.50, 'Unidade', 'Bebidas'),
            ('002', 'Pão Francês', 15.99, 'Peso', 'Padaria'), # Preço por KG
            ('003', 'Chocolate Barra 90g', 5.00, 'Unidade', 'Doces'),
            ('004', 'Queijo Muçarela', 32.00, 'Peso', 'Frios'), # Preço por KG
            ('005', 'Água Mineral 500ml', 2.50, 'Unidade', 'Bebidas'),
            ('006', 'Presunto Fatiado', 18.00, 'Peso', 'Frios'), # Preço por KG
            ('101', 'Bala de Goma', 0.10, 'Unidade', 'Doces'),
        ]
        
        cursor.executemany("""
            INSERT INTO Produtos (codigo, nome, preco, tipo_medicao, categoria) 
            VALUES (?, ?, ?, ?, ?)
        """, produtos_iniciais)

    conn.commit()

# ... (Restante do arquivo connect_db e get_all_categories permanecem inalterados)

def get_all_categories(conn):
    """Retorna uma lista de todas as categorias únicas de produtos."""
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categoria FROM Produtos ORDER BY categoria")
    return [row[0] for row in cursor.fetchall()]

