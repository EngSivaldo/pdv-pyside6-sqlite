# ui/cadastro_funcionario_dialog.py

import sqlite3
import hashlib
import datetime 
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QLabel, QPushButton, QComboBox, 
    QFormLayout, QVBoxLayout, QHBoxLayout, QMessageBox 
)
from PySide6.QtCore import Qt

class CadastroFuncionarioDialog(QDialog):
    """Diálogo para cadastrar/editar funcionários (Vendedor ou Admin)."""
    
    def __init__(self, db_connection, employee_id=None, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.employee_id = employee_id
        
        self.setup_ui()
        
        # Condição: Muda o comportamento da tela se estiver em modo edição
        if self.employee_id is not None:
            self.setWindowTitle("Editar Funcionário")
            self.load_employee_data()
        else:
            self.setWindowTitle("Cadastrar Novo Funcionário")
            
    # --- UI Setup ---
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 1. Nome Completo
        self.nome_input = QLineEdit()
        form_layout.addRow(QLabel("Nome Completo:"), self.nome_input)
        
        # 2. Login/Usuário
        self.login_input = QLineEdit()
        form_layout.addRow(QLabel("Login/Usuário:"), self.login_input)
        
        # 3. Senha 
        self.senha_input = QLineEdit()
        self.senha_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("Senha:"), self.senha_input)
        
        # 4. Confirmação de Senha (Nome CORRIGIDO para consistência)
        self.confirmar_senha_input = QLineEdit() 
        self.confirmar_senha_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("Confirme a Senha:"), self.confirmar_senha_input)
        
        # 5. Cargo (Nome CORRIGIDO para consistência)
        self.cargo_combo = QComboBox()
        self.cargo_combo.addItems(["vendedor", "admin"]) 
        form_layout.addRow(QLabel("Cargo/Nível:"), self.cargo_combo)
        
        main_layout.addLayout(form_layout)
        
        # Botões de Ação
        self.salvar_button = QPushButton("Salvar (F5)")
        self.cancelar_button = QPushButton("Cancelar")
        
        # Conexão dos botões
        self.salvar_button.clicked.connect(self.save_employee)
        self.cancelar_button.clicked.connect(self.reject) 
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.salvar_button)
        button_layout.addWidget(self.cancelar_button)
        
        main_layout.addLayout(button_layout)
        
    # --- Hash e Login/DB Lógica ---

    def hash_password(self, password):
        """Usa SHA-256 para gerar o hash da senha."""
        hashed_string = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return hashed_string

    # Em ui/cadastro_funcionario_dialog.py, dentro da classe CadastroFuncionarioDialog

    def save_employee(self):
        nome = self.nome_input.text().strip()
        login = self.login_input.text().strip()
        senha = self.senha_input.text()
        confirma_senha = self.confirmar_senha_input.text()
        cargo = self.cargo_combo.currentText()

        # --- 1. Validação Básica ---
        if not nome or not login:
            QMessageBox.warning(self, "Erro de Validação", "Nome e Login não podem estar vazios.")
            return

        # --- 2. Validação e Hashing da Senha ---
        senha_hash = None
        
        # A senha é validada e o hash é gerado SOMENTE se for um novo cadastro OU se houver texto nos campos de senha
        if self.employee_id is None or senha:
            if senha != confirma_senha:
                QMessageBox.critical(self, "Erro de Senha", "As senhas não coincidem.")
                return
            if len(senha) < 6:
                QMessageBox.critical(self, "Erro de Senha", "A senha deve ter pelo menos 6 caracteres.")
                return
            senha_hash = self.hash_password(senha)

        # --- 3. Operação de Banco de Dados (INSERT ou UPDATE) ---
        cursor = self.db_connection.cursor()

        if self.employee_id is None:
            # === MODO CADASTRO (INSERT) ===
            try:
                # 🛡️ FIX: Capturar e incluir a data de cadastro para resolver o erro NOT NULL
                data_cadastro = datetime.datetime.now().isoformat() 
                
                # 3.1. Verifica unicidade do login
                cursor.execute("SELECT COUNT(*) FROM Funcionarios WHERE login = ?", (login,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.critical(self, "Erro de Login", "Este login já está em uso.")
                    return
                
                # 3.2. Executa o INSERT (agora com data_cadastro)
                cursor.execute(
                    "INSERT INTO Funcionarios (nome, login, senha_hash, cargo, data_cadastro) VALUES (?, ?, ?, ?, ?)",
                    (nome, login, senha_hash, cargo, data_cadastro)
                )
                QMessageBox.information(self, "Sucesso", "Funcionário cadastrado com sucesso!")
                self.accept()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Erro no DB", f"Falha ao cadastrar: {e}")

        else:
            # === MODO EDIÇÃO (UPDATE) ===
            try:
                # Lógica de UPDATE permanece a mesma (sem alterar data_cadastro)
                if senha_hash:
                    cursor.execute(
                        "UPDATE Funcionarios SET nome = ?, senha_hash = ?, cargo = ? WHERE id = ?",
                        (nome, senha_hash, cargo, self.employee_id)
                    )
                    QMessageBox.information(self, "Sucesso", "Funcionário e senha atualizados com sucesso!")
                else:
                    cursor.execute(
                        "UPDATE Funcionarios SET nome = ?, cargo = ? WHERE id = ?",
                        (nome, cargo, self.employee_id)
                    )
                    QMessageBox.information(self, "Sucesso", "Funcionário atualizado com sucesso!")
                    
                self.accept()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Erro no DB", f"Falha ao atualizar: {e}")
                
        self.db_connection.commit()

    def load_employee_data(self):
        """Busca os dados do funcionário pelo ID e preenche os campos para edição."""
        cursor = self.db_connection.cursor()
        
        cursor.execute("SELECT nome, login, cargo FROM Funcionarios WHERE id = ?", 
                       (self.employee_id,))
        
        data = cursor.fetchone()
        
        if data:
            nome, login, cargo = data
            
            self.nome_input.setText(nome)
            self.login_input.setText(login)
            
            # Bloqueia o login em edição
            self.login_input.setEnabled(False) 
            
            # Define o valor do QComboBox (Cargo)
            index = self.cargo_combo.findText(cargo)
            if index != -1:
                self.cargo_combo.setCurrentIndex(index)
            
            # Ajusta os placeholders para indicar que a senha é opcional
            self.senha_input.setPlaceholderText("Deixe vazio para manter a senha atual.")
            self.confirmar_senha_input.setPlaceholderText("Deixe vazio para manter a senha atual.")
        else:
            QMessageBox.critical(self, "Erro", "Funcionário não encontrado.")
            self.reject()