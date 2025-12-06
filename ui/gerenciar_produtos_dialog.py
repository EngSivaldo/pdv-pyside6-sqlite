# ui/gerenciar_produtos_dialog.py (CÓDIGO CORRIGIDO)
import os
import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QMessageBox, QHeaderView
)
from PySide6.QtSql import QSqlTableModel, QSqlDatabase
from PySide6.QtCore import Qt
from ui.product_registration import ProductRegistrationWindow 
from ui.adjust_stock_dialog import AdjustStockDialog

class GerenciarProdutosDialog(QDialog):
    """Diálogo para listar, editar e excluir produtos, com restrição de acesso."""

    # ⭐️ MUDANÇA 1: Adicionar logged_user no __init__ ⭐️
    def __init__(self, db_connection: sqlite3.Connection, logged_user: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciamento de Produtos")
        self.db_connection = db_connection
        self.logged_user = logged_user # Armazena o usuário logado
        self.is_admin = self.logged_user.get('cargo') == 'admin' # Verifica o cargo
        
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
        
        # Cria os botões
        self.adjust_stock_button = QPushButton("➕ Ajustar Estoque Rápido")
        self.adjust_stock_button.setStyleSheet("background-color: #007BFF; color: white;")
        self.adjust_stock_button.clicked.connect(self.adjust_stock)
        
        self.edit_button = QPushButton("✏️ Editar Selecionado")
        self.edit_button.setStyleSheet("background-color: #FFA000; color: white;")
        self.edit_button.clicked.connect(self.edit_product)

        self.delete_button = QPushButton("❌ Excluir Selecionado")
        self.delete_button.setStyleSheet("background-color: #D32F2F; color: white;")
        self.delete_button.clicked.connect(self.delete_product)
        
        # ⭐️ MUDANÇA 2: Restringir a visibilidade dos botões ⭐️
        
        if self.is_admin:
            # Se for admin, adiciona todos os botões de controle
            button_layout.addWidget(self.adjust_stock_button) 
            button_layout.addStretch(1)
            button_layout.addWidget(self.edit_button)
            button_layout.addWidget(self.delete_button)
            button_layout.addStretch(1)
        else:
            # Se não for admin (vendedor), não adiciona os botões de edição/exclusão
            # Mas podemos adicionar uma label de aviso, se desejado
            # label_aviso = QLabel("Visualização: Apenas administradores podem modificar produtos.")
            # button_layout.addWidget(label_aviso)
            pass
        
        main_layout.addLayout(button_layout)
        
    def load_products(self):
        """Carrega os dados da tabela Produtos usando QSqlTableModel."""
        
        # FIX DE CONEXÃO: Obtendo o caminho exato do arquivo do banco de dados a partir da conexão sqlite3
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

        # ⭐️ AJUSTE DE CABEÇALHOS ⭐️
        # A ordem das colunas na tabela Produtos é: codigo, nome, preco, quantidade, tipo_medicao, categoria
        self.model.setHeaderData(0, Qt.Horizontal, "Código") # codigo (ID)
        self.model.setHeaderData(1, Qt.Horizontal, "Nome")
        self.model.setHeaderData(2, Qt.Horizontal, "Preço Unitário")
        self.model.setHeaderData(3, Qt.Horizontal, "Quantidade (Estoque)") # ⬅️ NOVO
        self.model.setHeaderData(4, Qt.Horizontal, "Medição")
        self.model.setHeaderData(5, Qt.Horizontal, "Categoria")

        self.table_view.setModel(self.model)
        
        # Ocultar o código é útil, mas é importante saber onde ele está (coluna 0)
        # self.table_view.hideColumn(0) 
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
            
    
    def adjust_stock(self):
        """Abre o diálogo de ajuste rápido para o produto selecionado e aplica a mudança."""
        
        selected_rows = self.table_view.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecione um produto para ajustar o estoque.")
            return

        selected_row = selected_rows[0].row()
        
        # Índices: 0=codigo, 1=nome, 3=quantidade (Estoque)
        code_index = self.model.index(selected_row, 0)
        name_index = self.model.index(selected_row, 1)
        qty_index = self.model.index(selected_row, 3) # ⬅️ Índice da Quantidade
        
        product_code = self.model.data(code_index)
        product_name = self.model.data(name_index)
        current_qty_raw = self.model.data(qty_index)
        # ⭐️ CORREÇÃO CRÍTICA: Converta o dado para float antes de usar ou passar ⭐️
        try:
            current_qty = float(current_qty_raw)
        except (ValueError, TypeError):
            # Se a conversão falhar (e.g., o campo estiver vazio ou for "None"), assuma 0.0
            current_qty = 0.0
            
        # 1. Abrir o Diálogo de Ajuste
        dialog = AdjustStockDialog(product_name, current_qty, self) # Agora 'current_qty' é float
        
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