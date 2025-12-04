# core/database.py

import sqlite3
from PySide6.QtWidgets import QMessageBox

def connect_db(window):
    """Conecta ou cria o arquivo de banco de dados SQLite."""
    try:
        conn = sqlite3.connect('pdv_database.db')
        print("Status BD: Conectado ao SQLite com sucesso.")
        return conn
    except sqlite3.Error as e:
        QMessageBox.critical(window, "Erro de Banco de Dados", 
                             f"Não foi possível conectar ao SQLite: {e}")
        return None

def create_and_populate_tables(conn):
    """Cria tabelas (Produtos e Vendas) e insere dados de exemplo."""
    try:
        cursor = conn.cursor()
        
        # Tabela de Produtos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Produtos (
                id INTEGER PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                tipo TEXT
            );
        """)
        
        # Tabela de Vendas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Vendas (
                id INTEGER PRIMARY KEY,
                data_hora TEXT NOT NULL,
                total REAL NOT NULL,
                troco REAL NOT NULL
            );
        """)

        # TAREFA EXTRA: Adicionar 'tipo' às linhas existentes (MIGRAÇÃO)
        try:
            cursor.execute("ALTER TABLE Produtos ADD COLUMN tipo TEXT")
            conn.commit()
            print("Status BD: Coluna 'tipo' adicionada à Produtos.")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                raise e

        # Insere dados de exemplo se a tabela estiver vazia
        cursor.execute("SELECT COUNT(*) FROM Produtos")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('1001', 'Maçã Unitária', 1.50, 'Alimentos'),
                ('1002', 'Leite Integral (1L)', 4.99, 'Alimentos'),
                ('1003', 'Pão de Forma', 7.80, 'Alimentos'),
                ('1004', 'Água Mineral (500ml)', 2.25, 'Bebidas'),
                ('2001', 'Detergente Limpa Fácil', 3.50, 'Limpeza'),
            ]
            cursor.executemany("INSERT INTO Produtos (codigo, nome, preco, tipo) VALUES (?, ?, ?, ?)", sample_products)
            conn.commit()
            print("Status BD: Dados de exemplo (com tipo) inseridos.")
        
        conn.commit()
        print("Status BD: Tabelas verificadas/criadas.")
        
    except sqlite3.Error as e:
        print(f"Erro ao criar/popular tabelas: {e}")