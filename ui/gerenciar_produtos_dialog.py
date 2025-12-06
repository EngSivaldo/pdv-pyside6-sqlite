# ui/gerenciar_produtos_dialog.py
import os
import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QMessageBox, QHeaderView
)
from PySide6.QtSql import QSqlTableModel, QSqlDatabase
from PySide6.QtCore import Qt
# Importar o diálogo de cadastro de produto (assumindo que o arquivo existe)
from ui.product_registration import ProductRegistrationWindow 

class GerenciarProdutosDialog(QDialog):
    """Diálogo para listar, editar e excluir produtos."""

    def __init__(self, db_connection: sqlite3.Connection, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciamento de Produtos")
        self.db_connection = db_connection
        self.resize(800, 500)
        
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. Tabela de Produtos (QTableView)
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        main_layout.addWidget(self.table_view)

        # 2. Botões de Ação
        button_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("✏️ Editar Selecionado")
        self.edit_button.setStyleSheet("background-color: #FFA000; color: white;")
        self.edit_button.clicked.connect(self.edit_product)

        self.delete_button = QPushButton("❌ Excluir Selecionado")
        self.delete_button.setStyleSheet("background-color: #D32F2F; color: white;")
        self.delete_button.clicked.connect(self.delete_product)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch(1)
        
        main_layout.addLayout(button_layout)
        
    def load_products(self):
        """Carrega os dados da tabela Produtos usando QSqlTableModel."""
        
        # FIX DE CONEXÃO: Obtendo o caminho exato do arquivo do banco de dados a partir da conexão sqlite3
        cursor = self.db_connection.cursor()
        cursor.execute("PRAGMA database_list")
        # O caminho do arquivo é o terceiro elemento (índice 2)
        db_path = cursor.fetchone()[2] 
        
        connection_name = "product_model_conn" 

        if QSqlDatabase.contains(connection_name):
            self.qt_db = QSqlDatabase.database(connection_name)
        else:
            self.qt_db = QSqlDatabase.addDatabase("QSQLITE", connection_name)
            self.qt_db.setDatabaseName(db_path) 
        
        if not self.qt_db.isOpen():
            if not self.qt_db.open():
                QMessageBox.critical(self, "Erro de Conexão Qt", 
                                     f"Não foi possível abrir a conexão Qt para o modelo: {self.qt_db.lastError().text()}")
                return
        
        # Inicializar o QSqlTableModel para a tabela Produtos
        self.model = QSqlTableModel(self, self.qt_db)
        self.model.setTable("Produtos")
        self.model.select()

        # Configurações do cabeçalho (Ajuste as colunas conforme sua tabela Produtos)
        self.model.setHeaderData(0, Qt.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Horizontal, "Nome")
        self.model.setHeaderData(2, Qt.Horizontal, "Preço Unitário")
        # ... Adicione mais headers conforme necessário

        self.table_view.setModel(self.model)
        
        # Oculta o ID (coluna 0)
        self.table_view.hideColumn(0) 
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def edit_product(self):
        """Abre o diálogo de cadastro no modo edição para o produto selecionado."""
        
        selected_indexes = self.table_view.selectedIndexes()
        
        if not selected_indexes:
            QMessageBox.warning(self, "Edição Necessária", "Selecione um produto para editar.")
            return
            
        # 1. Obter o ID do produto (Coluna 0)
        selected_row = selected_indexes[0].row()
        id_index = self.model.index(selected_row, 0)
        product_id = self.model.data(id_index)
        
        # 2. Abrir o diálogo de cadastro no MODO EDIÇÃO
        dialog = dialog = ProductRegistrationWindow(
            db_connection=self.db_connection, 
            product_id=product_id, 
            parent=self
        )
        
        # 3. Recarregar se o diálogo for aceito
        if dialog.exec() == QDialog.Accepted:
            self.load_products()

    def delete_product(self):
        """Exclui o produto selecionado após confirmação."""
        # 1. Verificar seleção
        selected_rows = self.table_view.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecione um produto para excluir.", QMessageBox.Ok)
            return

        # 2. Obter o nome do produto (Assumindo coluna 1)
        index = selected_rows[0]
        nome = self.model.data(self.model.index(index.row(), 1)) 
        
        # 3. Pedir Confirmação
        reply = QMessageBox.question(self, 'Confirmação', 
            f"Tem certeza que deseja excluir o produto '{nome}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 4. Executar Exclusão
            self.model.removeRow(index.row())
            if self.model.submitAll():
                QMessageBox.information(self, "Sucesso", f"Produto '{nome}' excluído.", QMessageBox.Ok)
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir o produto: {self.model.lastError().text()}", QMessageBox.Ok)
            
            # 5. Recarregar a lista
            self.load_products()