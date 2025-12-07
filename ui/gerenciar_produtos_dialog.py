import os
import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QMessageBox, QHeaderView, QLabel
)
from PySide6.QtSql import QSqlTableModel, QSqlDatabase
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlError 
from ui.product_registration import ProductRegistrationWindow 
from ui.adjust_stock_dialog import AdjustStockDialog

class GerenciarProdutosDialog(QDialog):
    """Diálogo para listar, editar e excluir produtos, com restrição de acesso."""

    def __init__(self, db_connection: sqlite3.Connection, logged_user: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciamento de Produtos")
        self.db_connection = db_connection
        self.logged_user = logged_user 
        self.is_admin = self.logged_user.get('cargo') == 'admin' 
        
        self.resize(1000, 600) # Aumentado para caber mais colunas
        
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
        
        # Cria os botões
        self.adjust_stock_button = QPushButton("➕ Ajustar Estoque Rápido")
        self.adjust_stock_button.setStyleSheet("background-color: #007BFF; color: white; padding: 10px 15px;")
        self.adjust_stock_button.clicked.connect(self.adjust_stock)
        
        self.edit_button = QPushButton("✏️ Editar Selecionado")
        self.edit_button.setStyleSheet("background-color: #FFA000; color: white; padding: 10px 15px;")
        self.edit_button.clicked.connect(self.edit_product)

        self.delete_button = QPushButton("❌ Excluir Selecionado")
        self.delete_button.setStyleSheet("background-color: #D32F2F; color: white; padding: 10px 15px;")
        self.delete_button.clicked.connect(self.delete_product)
        
        # Lógica de Visibilidade:
        
        # Ajustar Estoque Rápido é visível para todos (pode ser usado como inventário)
        button_layout.addWidget(self.adjust_stock_button) 
        button_layout.addStretch(1) # Espaçamento
        
        # Edição e Exclusão são apenas para Admin
        if self.is_admin:
            button_layout.addWidget(self.edit_button)
            button_layout.addWidget(self.delete_button)
        else:
            # Garante que, se o vendedor estiver logado, não haja botões vazios no meio
            pass

        main_layout.addLayout(button_layout)
        
    def load_products(self):
        """Carrega os dados da tabela Produtos usando QSqlTableModel."""
        
        cursor = self.db_connection.cursor()
        cursor.execute("PRAGMA database_list")
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

        # ⭐️ AJUSTE DE CABEÇALHOS (BASEADO NA ORDEM REAL DO DB: id, codigo, nome, preco, quantidade, tipo_medicao, categoria, ativo) ⭐️
        
        # Coluna 0: id (oculta)
        self.model.setHeaderData(0, Qt.Horizontal, "ID") 
        # Coluna 1: codigo 
        self.model.setHeaderData(1, Qt.Horizontal, "Código") 
        # Coluna 2: nome
        self.model.setHeaderData(2, Qt.Horizontal, "Nome")
        # Coluna 3: preco
        self.model.setHeaderData(3, Qt.Horizontal, "Preço Un.") 
        # Coluna 4: quantidade 
        self.model.setHeaderData(4, Qt.Horizontal, "Estoque") 
        # Coluna 5: tipo_medicao
        self.model.setHeaderData(5, Qt.Horizontal, "Medição")
        # Coluna 6: categoria
        self.model.setHeaderData(6, Qt.Horizontal, "Categoria")
        # Coluna 7: ativo (oculta)
        self.model.setHeaderData(7, Qt.Horizontal, "Ativo") 

        self.table_view.setModel(self.model)
        
        # Ocultar colunas desnecessárias (ID e Ativo)
        self.table_view.hideColumn(0) 
        # self.table_view.hideColumn(7) # Manter Ativo visível pode ser útil para debug/gestão
        
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Garante que o Nome estique
        
        
    def edit_product(self):
        """Abre o diálogo de cadastro no modo edição para o produto selecionado."""
        
        selected_indexes = self.table_view.selectedIndexes()
        
        if not selected_indexes:
            QMessageBox.warning(self, "Edição Necessária", "Selecione um produto para editar.")
            return
            
        # 1. Obter o ID interno do produto (Coluna 0, o ID primário)
        selected_row = selected_indexes[0].row()
        id_index = self.model.index(selected_row, 0)
        product_id = self.model.data(id_index)
        
        # 2. Abrir o diálogo de cadastro no MODO EDIÇÃO
        dialog = ProductRegistrationWindow(
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

        # 2. Obter o nome do produto (Coluna 2)
        index = selected_rows[0]
        nome = self.model.data(self.model.index(index.row(), 2)) 
        
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
            
    
    def adjust_stock(self):
        """Abre o diálogo de ajuste rápido para o produto selecionado e aplica a mudança."""
        
        selected_rows = self.table_view.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecione um produto para ajustar o estoque.")
            return

        selected_row = selected_rows[0].row()
        
        # ⭐️ ÍNDICES CORRETOS: 0=id, 1=codigo, 2=nome, 3=preco, 4=quantidade ⭐️
        code_index = self.model.index(selected_row, 1)
        name_index = self.model.index(selected_row, 2)
        qty_index = self.model.index(selected_row, 4) # CORRIGIDO: 4 é 'quantidade'
        
        product_code = self.model.data(code_index)
        product_name = self.model.data(name_index)
        current_qty_raw = self.model.data(qty_index)
        
        try:
            current_qty = float(current_qty_raw)
        except (ValueError, TypeError, QSqlError):
            current_qty = 0.0
            
        # 1. Abrir o Diálogo de Ajuste
        dialog = AdjustStockDialog(product_name, current_qty, self)
        
        if dialog.exec() == QDialog.Accepted:
            adjustment = dialog.get_adjustment()
            
            if adjustment != 0:
                # 2. Chamar função do DB para aplicar o ajuste
                success = self._apply_stock_adjustment(product_code, adjustment)
                
                if success:
                    QMessageBox.information(self, "Sucesso", f"Estoque de '{product_name}' ajustado em {adjustment:+.2f}.")
                    self.load_products() # Recarrega a tabela para mostrar o novo valor
                else:
                    QMessageBox.critical(self, "Erro DB", "Falha ao atualizar o estoque no banco de dados.")

    def _apply_stock_adjustment(self, product_code, adjustment):
        """Função interna para aplicar o ajuste de estoque no banco de dados."""
        if not self.db_connection: return False
        
        try:
            cursor = self.db_connection.cursor()
            # Adiciona o ajuste ao valor atual do estoque
            query = "UPDATE Produtos SET quantidade = quantidade + ? WHERE codigo = ?"
            cursor.execute(query, (adjustment, product_code))
            self.db_connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao aplicar ajuste de estoque: {e}")
            self.db_connection.rollback()
            return False