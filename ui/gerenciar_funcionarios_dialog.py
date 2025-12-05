# ui/gerenciar_funcionarios_dialog.py
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QMessageBox, QHeaderView
)
from PySide6.QtSql import QSqlTableModel, QSqlDatabase
from PySide6.QtCore import Qt
# Importação da tela de cadastro/edição
from ui.cadastro_funcionario_dialog import CadastroFuncionarioDialog 

class GerenciarFuncionariosDialog(QDialog):
    """Diálogo para listar, editar e excluir funcionários."""

    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciamento de Funcionários (Admin)")
        self.db_connection = db_connection
        self.resize(800, 500)
        
        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. Tabela de Funcionários (QTableView)
        self.table_view = QTableView()
        # Permite selecionar linhas inteiras
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        main_layout.addWidget(self.table_view)

        # 2. Botões de Ação
        button_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("✏️ Editar Selecionado")
        self.edit_button.setStyleSheet("background-color: #FFA000; color: white;")
        self.edit_button.clicked.connect(self.edit_employee)

        self.delete_button = QPushButton("❌ Excluir Selecionado")
        self.delete_button.setStyleSheet("background-color: #D32F2F; color: white;")
        self.delete_button.clicked.connect(self.delete_employee)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch(1)
        
        main_layout.addLayout(button_layout)
        
    def load_employees(self):
        """Carrega os dados da tabela Funcionarios usando QSqlTableModel."""
        
        # 1. CONFIGURANDO A PONTE DE CONEXÃO QT
        
        # FIX DEFINITIVO: Obtendo o caminho exato do arquivo do banco de dados a partir da conexão sqlite3
        cursor = self.db_connection.cursor()
        cursor.execute("PRAGMA database_list")
        # O caminho do arquivo é o terceiro elemento (índice 2) do resultado
        db_path = cursor.fetchone()[2] 
        
        connection_name = "employee_model_conn" # Nome único para esta conexão Qt

        # Verifica se a conexão já existe no sistema Qt (para evitar erros de nome duplicado)
        if QSqlDatabase.contains(connection_name):
            self.qt_db = QSqlDatabase.database(connection_name)
        else:
            self.qt_db = QSqlDatabase.addDatabase("QSQLITE", connection_name)
            self.qt_db.setDatabaseName(db_path) # Usando o caminho obtido via PRAGMA
        
        # Abre a conexão Qt
        if not self.qt_db.isOpen():
            if not self.qt_db.open():
                QMessageBox.critical(self, "Erro de Conexão Qt", 
                                     f"Não foi possível abrir a conexão Qt para o modelo: {self.qt_db.lastError().text()}")
                return
        
        # 2. Inicializar o QSqlTableModel
        self.model = QSqlTableModel(self, self.qt_db)
        self.model.setTable("Funcionarios")
        
        # Filtro: não mostra o admin mestre
        self.model.setFilter("login != 'admin_mestre'") 
        
        # Executa a seleção e atualiza os dados
        self.model.select()
        print(f"Qt Model Row Count: {self.model.rowCount()}") # Saída de depuração
        
        # Configurações do cabeçalho
        self.model.setHeaderData(0, Qt.Horizontal, "ID")
        self.model.setHeaderData(1, Qt.Horizontal, "Nome")
        self.model.setHeaderData(2, Qt.Horizontal, "Login")
        self.model.setHeaderData(4, Qt.Horizontal, "Cargo")
        self.model.setHeaderData(5, Qt.Horizontal, "Data Cadastro")

        self.table_view.setModel(self.model)
        
        # Oculta o Hash da Senha (coluna 3) e o ID (coluna 0)
        self.table_view.hideColumn(0)
        self.table_view.hideColumn(3) 

        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def edit_employee(self):
        """Abre o diálogo de cadastro no modo edição para o funcionário selecionado."""
        
        selected_indexes = self.table_view.selectedIndexes()
        
        if not selected_indexes:
            QMessageBox.warning(self, "Edição Necessária", "Selecione um funcionário para editar.")
            return

        # Obter o ID do funcionário (ID está na coluna 0)
        selected_row = selected_indexes[0].row()
        id_index = self.model.index(selected_row, 0)
        employee_id = self.model.data(id_index)
        
        # Abrir o diálogo de cadastro no MODO EDIÇÃO
        dialog = CadastroFuncionarioDialog(
            db_connection=self.db_connection, 
            employee_id=employee_id, 
            parent=self
        )
        
        # Se o diálogo for aceito (dados salvos), recarregar a lista
        if dialog.exec() == QDialog.Accepted:
            self.load_employees()

    def delete_employee(self):
        """Exclui o funcionário selecionado."""
        selected_rows = self.table_view.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecione um funcionário para excluir.", QMessageBox.Ok)
            return

        index = selected_rows[0]
        # Pega o nome para a mensagem de confirmação (coluna 1)
        nome = self.model.data(self.model.index(index.row(), 1)) 
        
        reply = QMessageBox.question(self, 'Confirmação', 
            f"Tem certeza que deseja excluir o funcionário '{nome}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Remove a linha do modelo e envia a mudança para o banco de dados
            self.model.removeRow(index.row())
            if self.model.submitAll():
                QMessageBox.information(self, "Sucesso", f"Funcionário '{nome}' excluído.", QMessageBox.Ok)
            else:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir o funcionário: {self.model.lastError().text()}", QMessageBox.Ok)
            
            # Recarrega a lista para garantir que a tabela está sincronizada
            self.load_employees()