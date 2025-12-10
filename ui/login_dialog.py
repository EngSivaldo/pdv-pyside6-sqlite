# ui/login_dialog.py

from PySide6.QtWidgets import (
    QDialog, QLineEdit, QLabel, QPushButton, QVBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
import hashlib
import sqlite3
import sys
from .cadastro_funcionario_dialog import CadastroFuncionarioDialog # Importa para o primeiro acesso

class LoginDialog(QDialog):
    """Diálogo modal para autenticação de funcionários."""

    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acesso ao PDV - Login")
        self.db_connection = db_connection
        self.user_data = None 
        self.setFixedSize(400, 300) 
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint) 
        self.setup_ui()
        self.check_for_first_admin()

    def hash_password(self, password):
        """Gera o hash da senha usando o mesmo método do cadastro (SHA-256)."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    # ❌ MÉTODO _apply_modern_style REMOVIDO ❌

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Configura o QDialog como o 'cartão' de login
        self.setObjectName("loginCard") 

        # --- Título (ID: #loginTitle) ---
        title_label = QLabel("ACESSO RESTRITO 🔒")
        title_label.setObjectName("loginTitle") 
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # --- Campos de Login ---
        
        # Rótulo Usuário (ID: #fieldLabel)
        user_label = QLabel("Usuário:")
        user_label.setObjectName("fieldLabel") 
        main_layout.addWidget(user_label)
        
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Login / Nome de Usuário")
        self.login_input.setObjectName("inputField") # Ajustado para #inputField
        main_layout.addWidget(self.login_input)

        # Rótulo Senha (ID: #fieldLabel)
        senha_label = QLabel("Senha:")
        senha_label.setObjectName("fieldLabel") 
        main_layout.addWidget(senha_label)
        
        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        self.senha_input.setObjectName("inputField") # Ajustado para #inputField
        main_layout.addWidget(self.senha_input)

        # --- Botão de Login (ID: #loginButton) ---
        self.login_button = QPushButton("✅ Entrar")
        self.login_button.setObjectName("loginButton") 
        self.login_button.clicked.connect(self.handle_login)
        
        self.login_input.returnPressed.connect(self.handle_login)
        self.senha_input.returnPressed.connect(self.handle_login)
        main_layout.addWidget(self.login_button)
        
        # --- Botão de Sair (ID: #exitButton) ---
        self.exit_button = QPushButton("❌ Sair do Sistema")
        self.exit_button.setObjectName("exitButton") 
        self.exit_button.clicked.connect(self.close) 
        main_layout.addWidget(self.exit_button)
        
        self.login_input.setFocus()
        

    def check_for_first_admin(self):
        """Verifica se há funcionários. Se não houver, força o cadastro do Administrador Mestre."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Funcionarios")
        if cursor.fetchone()[0] == 0:
            QMessageBox.information(self, 'Primeiro Acesso', 
                                     "Nenhum funcionário cadastrado. Por favor, cadastre o Administrador Mestre.",
                                     QMessageBox.Ok)
            admin_dialog = CadastroFuncionarioDialog(self.db_connection)
            admin_dialog.setWindowTitle("Cadastro do Administrador Mestre")
            if admin_dialog.exec() != QDialog.Accepted:
                sys.exit(0) 

    def handle_login(self):
        login = self.login_input.text().strip()
        senha_digitada = self.senha_input.text()

        if not login or not senha_digitada:
            QMessageBox.warning(self, "Erro de Login", "Por favor, preencha o login e a senha.")
            return

        senha_hash_digitada = self.hash_password(senha_digitada)

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT id, nome, login, senha_hash, cargo FROM Funcionarios WHERE login = ?", (login,))
            result = cursor.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "Erro de DB", f"Falha na busca: {e}")
            return

        if result:
            id_db, nome_db, login_db, senha_hash_db, cargo_db = result

            if senha_hash_db == senha_hash_digitada:
                self.user_data = {
                    'id': id_db, 
                    'nome': nome_db, 
                    'login': login_db, 
                    'cargo': cargo_db
                }
                self.accept()
            else:
                QMessageBox.critical(self, "Erro de Login", "Senha incorreta.")
        else:
            QMessageBox.critical(self, "Erro de Login", "Usuário não encontrado.")