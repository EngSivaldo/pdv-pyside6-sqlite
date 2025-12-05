# ui/product_list.py - CORRIGIDO PARA 5 COLUNAS E CATEGORIAS DINÂMICAS

import sqlite3
from unidecode import unidecode
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableView, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem


# Funções de normalização de texto (Mantidas)
def normalize_text(text):
    """Converte o texto para minúsculas e remove acentos/cedilhas."""
    if text is None:
        return ""
    text_str = str(text).strip()
    normalized = unidecode(text_str)
    return normalized.lower()

def clean_for_comparison(text):
    """Remove caracteres especiais, espaços e pontuações do texto normalizado."""
    normalized = normalize_text(text)
    cleaned = re.sub(r'[^a-z0-9]', '', normalized)
    return cleaned


class ProductListWindow(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        self.setWindowTitle("Consulta e Gerenciamento de Produtos")
        self.setGeometry(150, 150, 900, 600) # Aumentado para caber 5 colunas
        self.db_connection = db_connection
        
        self.model = None # Inicializa o modelo
        
        self._setup_ui()
        self._load_categories_and_populate_combo() # ⭐️ NOVO: Carrega as categorias antes de tudo
        self.load_products()

    def _setup_ui(self):
        """Configura o layout e os widgets da tela de consulta."""
        main_layout = QVBoxLayout(self)
        
        # --- 1. Filtros (Categoria e Texto) ---
        header_layout = QHBoxLayout()
        
        # Filtro por Categoria (QComboBox)
        header_layout.addWidget(QLabel("📦 Filtrar por Categoria:"))
        self.category_filter_input = QComboBox() # ⭐️ RENOMEADO para refletir 'categoria'
        self.category_filter_input.setFont(QFont("Arial", 12))
        # O sinal será conectado após carregar as categorias
        
        header_layout.addWidget(self.category_filter_input)
        
        # Filtro por Nome/Código (QLineEdit)
        header_layout.addWidget(QLabel("🔍 Digite para Filtrar (Nome/Código/Medida):"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por Código, Nome ou Tipo de Medida...")
        self.search_input.setFont(QFont("Arial", 12))
        
        self.search_input.editingFinished.connect(self.filter_products) 
        
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

    def _load_categories_and_populate_combo(self):
        """Busca as categorias distintas do BD e preenche o ComboBox."""
        if not self.db_connection:
            return
            
        try:
            cursor = self.db_connection.cursor()
            # ⭐️ NOVO: Usando a coluna 'categoria'
            cursor.execute("SELECT DISTINCT categoria FROM Produtos ORDER BY categoria") 
            categories = [row[0] for row in cursor.fetchall()]
            
            # Limpa e adiciona "Todos" e as categorias encontradas
            self.category_filter_input.clear()
            self.category_filter_input.addItem("Todos")
            self.category_filter_input.addItems(categories)
            
            # Conecta o sinal após a população inicial
            self.category_filter_input.currentTextChanged.connect(self.load_products)
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de BD", f"Erro ao carregar categorias: {e}")
            
    def load_products(self):
        """Busca produtos no BD, aplicando o filtro de Categoria via SQL."""
        if not self.db_connection:
            QMessageBox.critical(self, "Erro de BD", "Conexão com o banco de dados indisponível.")
            return

        selected_category = self.category_filter_input.currentText()
        
        # ⭐️ CORREÇÃO CRÍTICA: Selecionando as 5 colunas
        sql_query = "SELECT codigo, nome, preco, tipo_medicao, categoria FROM Produtos" 
        params = []
        
        if selected_category and selected_category != "Todos":
            # ⭐️ Filtrando pela coluna 'categoria'
            sql_query += " WHERE categoria = ?"
            params.append(selected_category)
            
        sql_query += " ORDER BY codigo"

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(sql_query, tuple(params))
            products = cursor.fetchall()

            # --- SETUP DO MODELO ---
            # ⭐️ CORREÇÃO CRÍTICA: O modelo agora tem 5 colunas
            self.model = QStandardItemModel(0, 5) 
            self.model.setHorizontalHeaderLabels(["CÓDIGO", "NOME", "PREÇO", "MEDIDA", "CATEGORIA"]) # ⭐️ NOVOS NOMES
            
            for row_data in products:
                # ⭐️ CORREÇÃO CRÍTICA: Desempacotando 5 valores
                codigo, nome, preco, tipo_medicao, categoria = row_data 
                
                row = []
                
                # 0. Código
                item_code = QStandardItem(codigo)
                item_code.setTextAlignment(Qt.AlignCenter)
                row.append(item_code)
                
                # 1. Nome
                row.append(QStandardItem(nome))
                
                # 2. Preço
                item_price = QStandardItem(f"R$ {preco:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
                item_price.setTextAlignment(Qt.AlignRight)
                row.append(item_price)
                
                # 3. Tipo de Medida (Peso/Unidade) - Índice 3
                item_medida = QStandardItem(tipo_medicao)
                item_medida.setTextAlignment(Qt.AlignCenter)
                row.append(item_medida)
                
                # 4. Categoria - Índice 4
                item_category = QStandardItem(categoria)
                item_category.setTextAlignment(Qt.AlignCenter)
                row.append(item_category)
                
                self.model.appendRow(row)

            self.product_table.setModel(self.model)
            
            # Configuração de Colunas (Índices 0 a 4)
            self.product_table.setColumnWidth(0, 100) 
            self.product_table.setColumnWidth(1, 220)
            self.product_table.setColumnWidth(2, 100)
            self.product_table.setColumnWidth(3, 100)
            self.product_table.setColumnWidth(4, 150)
            
            # Re-aplica o filtro de texto
            self.filter_products(self.search_input.text())
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de BD", f"Erro ao carregar produtos: {e}")

    def filter_products(self, text):
        """
        Filtra os produtos visíveis na tabela, buscando em Código, Nome, Tipo de Medida e Categoria.
        """
        
        if not hasattr(self, 'model') or not self.model:
            return

        search_text = clean_for_comparison(text)
        
        for row in range(self.model.rowCount()):
            
            if self.model.columnCount() < 5:
                # Se o modelo não foi carregado corretamente (menos de 5 colunas), pula o filtro.
                self.product_table.setRowHidden(row, False)
                continue
            
            # 2. Obtém os dados das colunas (agora 5 índices)
            item_code_text = self.model.item(row, 0).text()
            item_name_text = self.model.item(row, 1).text()
            # ⭐️ NOVO: Índice 3 e 4
            item_medida_text = self.model.item(row, 3).text() 
            item_categoria_text = self.model.item(row, 4).text()
            
            # TRATAMENTO CRÍTICO: Limpa o texto da tabela
            item_name_text = item_name_text.replace('\n', '').replace('\r', '').strip()

            # 3. Limpa e normaliza os dados da tabela
            code = clean_for_comparison(item_code_text)
            name = clean_for_comparison(item_name_text)
            medida_clean = clean_for_comparison(item_medida_text) # NOVO
            categoria_clean = clean_for_comparison(item_categoria_text) # NOVO
            
            # 4. Compara a string totalmente limpa em CÓDIGO, NOME, MEDIDA ou CATEGORIA
            is_visible = (search_text in code or 
                          search_text in name or
                          search_text in medida_clean or
                          search_text in categoria_clean) 
            
            self.product_table.setRowHidden(row, not is_visible)