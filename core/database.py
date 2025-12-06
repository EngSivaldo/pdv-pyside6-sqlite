import sqlite3
import os
from datetime import datetime

# Usamos um hash de senha seguro para um administrador inicial (ex: 'admin' hasheado)
# Nota: Você deve usar uma biblioteca como 'bcrypt' em produção, mas usaremos uma string simples aqui.
DEFAULT_ADMIN_PASSWORD_HASH = "pbkdf2:sha256:260000$P2N5G7c6W7oM0Z4R$8612f0f0c0573e3a47926b0a701d09e755298a85f817454238e55e378f85f02c" 

DB_NAME = 'pdv.db'

# --- FUNÇÕES DE CONEXÃO E INICIALIZAÇÃO ---

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
    popula as tabelas se estiverem vazias.
    """
    if conn is None:
        return

    cursor = conn.cursor()

    # 1. Tabela Produtos 
    # ⭐️ CORREÇÃO CRÍTICA: Adicionando a coluna 'quantidade' REAL ⭐️
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Produtos (
            codigo TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade REAL DEFAULT 0,  -- ⬅️ NOVO: Coluna de Estoque
            tipo_medicao TEXT NOT NULL, 
            categoria TEXT NOT NULL 
        )
    """)
    
    # Adiciona a coluna 'quantidade' para quem já tinha o banco criado sem ela (Retrocompatibilidade)
    try:
        cursor.execute("ALTER TABLE Produtos ADD COLUMN quantidade REAL DEFAULT 0")
        print("LOG: Coluna 'quantidade' adicionada à tabela 'Produtos'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise

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
            id_funcionario INTEGER,  -- ⬅️ Mantido aqui para garantir
            FOREIGN KEY (id_funcionario) REFERENCES Funcionarios(id)
        )
    """)
    
    # Tenta adicionar id_funcionario para compatibilidade reversa
    try:
        cursor.execute("ALTER TABLE Vendas ADD COLUMN id_funcionario INTEGER")
        print("LOG: Coluna 'id_funcionario' adicionada à tabela 'Vendas'.")
    except sqlite3.OperationalError:
        pass # Coluna já existe

    # 4. Tabela ItensVenda
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
        # ⭐️ NOVO: Adicionamos um valor inicial de estoque (o 4º item na tupla)
        produtos_iniciais = [
            ('001', 'Refrigerante Cola 2L', 7.50, 50.0, 'Unidade', 'Bebidas'),
            ('002', 'Pão Francês', 15.99, 10.0, 'Peso', 'Padaria'), # 10 kg
            ('003', 'Chocolate Barra 90g', 5.00, 100.0, 'Unidade', 'Doces'),
            ('004', 'Queijo Muçarela', 32.00, 5.0, 'Peso', 'Frios'), # 5 kg
            ('005', 'Água Mineral 500ml', 2.50, 200.0, 'Unidade', 'Bebidas'),
            ('006', 'Presunto Fatiado', 18.00, 8.0, 'Peso', 'Frios'), # 8 kg
            ('101', 'Bala de Goma', 0.10, 500.0, 'Unidade', 'Doces'),
        ]
        
        cursor.executemany("""
            INSERT INTO Produtos (codigo, nome, preco, quantidade, tipo_medicao, categoria) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, produtos_iniciais)
        print("LOG: Produtos iniciais populados.")

    # Popula Administrador Inicial (Se não houver nenhum funcionário)
    cursor.execute("SELECT COUNT(*) FROM Funcionarios")
    if cursor.fetchone()[0] == 0:
        # A senha real para 'admin' é '123'
        admin_data = ('Admin Master', 'admin', DEFAULT_ADMIN_PASSWORD_HASH, 'admin', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        cursor.execute("""
            INSERT INTO Funcionarios (nome, login, senha_hash, cargo, data_cadastro) 
            VALUES (?, ?, ?, ?, ?)
        """, admin_data)
        print("LOG: Administrador inicial (admin/123) criado.")

    conn.commit()


# --- FUNÇÃO DE DECREMENTO DE ESTOQUE E FINALIZAÇÃO DE VENDA ---

def finalizar_venda(db_conn: sqlite3.Connection, itens_venda, total, recebido, troco, id_funcionario):
    """
    Finaliza a transação, registra nas tabelas Vendas e ItensVenda, 
    e atualiza (decrementa) o estoque dos produtos vendidos.
    """
    try:
        cursor = db_conn.cursor() 
        
        # 1. Inserir na tabela Vendas
        cursor.execute("""
            INSERT INTO Vendas (data_hora, total_venda, valor_recebido, troco, id_funcionario) 
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, recebido, troco, id_funcionario))
        
        # 2. Obter o ID da Venda
        venda_id = cursor.lastrowid
        
        # ⭐️ 3. LÓGICA DE DECREMENTO DE ESTOQUE (AGORA FUNCIONAL) ⭐️
        for codigo, nome, quantidade_vendida, preco in itens_venda:
            
            # Subtrai a 'quantidade_vendida' da coluna 'quantidade' (estoque)
            cursor.execute("""
                UPDATE Produtos
                SET quantidade = quantidade - ?
                WHERE codigo = ?
            """, (quantidade_vendida, codigo))
        
        # 4. Preparar e Inserir na tabela ItensVenda
        itens_venda_data = []
        for codigo, nome, quantidade, preco in itens_venda:
            itens_venda_data.append((venda_id, codigo, nome, quantidade, preco))
            
        cursor.executemany("""
            INSERT INTO ItensVenda (venda_id, produto_codigo, nome_produto, quantidade, preco_unitario) 
            VALUES (?, ?, ?, ?, ?)
        """, itens_venda_data)
        
        # 5. Confirmar todas as operações no banco de dados
        db_conn.commit()
        
        return venda_id 
        
    except sqlite3.Error as e:
        print(f"ERRO ao finalizar a venda: {e}")
        db_conn.rollback()
        return None 

# --- OUTRAS FUNÇÕES ---

def get_all_categories(conn):
    """Retorna uma lista de todas as categorias únicas de produtos."""
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categoria FROM Produtos ORDER BY categoria")
    return [row[0] for row in cursor.fetchall()]

# Exemplo de função (se você já a tiver) em core/database.py

def get_all_products(conn):
    if conn is None:
        return []
    cursor = conn.cursor()
    # ⭐️ Corrija a consulta para incluir a coluna 'quantidade' ⭐️
    cursor.execute("""
        SELECT codigo, nome, preco, quantidade, tipo_medicao, categoria 
        FROM Produtos 
        ORDER BY nome
    """)
    return cursor.fetchall()