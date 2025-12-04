# ui/product_list.py

import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableView, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem

# Lista de categorias (deve ser compatível com product_registration.py)
CATEGORY_LIST = ["Todos", "Alimentos", "Bebidas", "Limpeza", "Higiene Pessoal", "Eletrônicos", "Outros"]

class ProductListWindow(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        self.setWindowTitle("Consulta e Gerenciamento de Produtos")
        self.setGeometry(150, 150, 800, 600)
        self.db_connection = db_connection
        
        self._setup_ui()
        self.load_products()

    def _setup_ui(self):
        """Configura o layout e os widgets da tela de consulta."""
        main_layout = QVBoxLayout(self)
        
        # --- 1. Filtros (Tipo e Texto) ---
        header_layout = QHBoxLayout()
        
        # Filtro por Tipo (QComboBox)
        header_layout.addWidget(QLabel("📦 Filtrar por Tipo:"))
        self.type_filter_input = QComboBox()
        self.type_filter_input.setFont(QFont("Arial", 12))
        self.type_filter_input.addItems(CATEGORY_LIST) 
        self.type_filter_input.currentTextChanged.connect(self.load_products) # Recarrega ao mudar o tipo
        header_layout.addWidget(self.type_filter_input)
        
        # Filtro por Nome/Código (QLineEdit)
        header_layout.addWidget(QLabel("🔍 Digite para Filtrar (Nome/Código):"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por Código ou Nome...")
        self.search_input.setFont(QFont("Arial", 12))
        self.search_input.textChanged.connect(self.filter_products) 
        header_layout.addWidget(self.search_input)
        
        main_layout.addLayout(header_layout)
        
        # --- 2. Tabela de Produtos (QTableView) ---
        self.product_table = QTableView()
        main_layout.addWidget(self.product_table)
        
        # --- 3. Botões de Ação ---
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 Atualizar Lista")
        refresh_button.clicked.connect(self.load_products)
        button_layout.addWidget(refresh_button)
        
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept) 
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)

    def load_products(self):
        """Busca produtos no BD, aplicando o filtro de tipo se necessário."""
        if not self.db_connection:
            QMessageBox.critical(self, "Erro de BD", "Conexão com o banco de dados indisponível.")
            return

        selected_type = self.type_filter_input.currentText()
        sql_query = "SELECT id, codigo, nome, preco, tipo FROM Produtos"
        params = []
        
        if selected_type and selected_type != "Todos":
            sql_query += " WHERE tipo = ?"
            params.append(selected_type)
            
        sql_query += " ORDER BY codigo"

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(sql_query, tuple(params))
            products = cursor.fetchall()

            self.model = QStandardItemModel(0, 5) 
            self.model.setHorizontalHeaderLabels(["ID", "CÓDIGO", "NOME", "PREÇO", "TIPO"])

            for row_data in products:
                row = []
                # 0. ID (Oculto)
                row.append(QStandardItem(str(row_data[0])))
                
                # 1. Código
                item_code = QStandardItem(row_data[1])
                item_code.setTextAlignment(Qt.AlignCenter)
                row.append(item_code)
                
                # 2. Nome
                row.append(QStandardItem(row_data[2]))
                
                # 3. Preço
                item_price = QStandardItem(f"R$ {row_data[3]:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
                item_price.setTextAlignment(Qt.AlignRight)
                row.append(item_price)
                
                # 4. TIPO
                item_type = QStandardItem(row_data[4])
                item_type.setTextAlignment(Qt.AlignCenter)
                row.append(item_type)
                
                self.model.appendRow(row)

            self.product_table.setModel(self.model)
            
            # Configurações de exibição da tabela
            self.product_table.setColumnWidth(1, 100) 
            self.product_table.setColumnWidth(2, 250)
            self.product_table.setColumnWidth(3, 100)
            self.product_table.setColumnWidth(4, 150)
            self.product_table.setColumnHidden(0, True) 

            # Re-aplica o filtro de texto se houver algo digitado
            self.filter_products(self.search_input.text())
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de BD", f"Erro ao carregar produtos: {e}")


    def filter_products(self, text):
        """Filtra os produtos visíveis na tabela baseado no texto de busca."""
        if not hasattr(self, 'model'):
            return

        for row in range(self.model.rowCount()):
            code = self.model.item(row, 1).text().lower()
            name = self.model.item(row, 2).text().lower()
            
            search_text = text.lower().strip()
            
            is_visible = search_text in code or search_text in name
            
            self.product_table.setRowHidden(row, not is_visible)