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
        self.user_data = None # Armazenará (id, nome, login, cargo) do usuário logado
        self.setFixedSize(400, 250) 
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint) # Opcional: manter botões básicos
        self.setup_ui()
        self.check_for_first_admin() # Verifica a necessidade de criar o admin

    def hash_password(self, password):
        """Gera o hash da senha usando o mesmo método do cadastro (SHA-256)."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Título
        title_label = QLabel("ACESSO RESTRITO")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Campos de Login
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Login / Nome de Usuário")
        
        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        
        main_layout.addWidget(QLabel("Usuário:"))
        main_layout.addWidget(self.login_input)
        main_layout.addWidget(QLabel("Senha:"))
        main_layout.addWidget(self.senha_input)

        # Botão de Login
        self.login_button = QPushButton("Entrar")
        self.login_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.login_button.clicked.connect(self.handle_login)
        
        # Conecta Enter ao botão de login
        self.login_input.returnPressed.connect(self.handle_login)
        self.senha_input.returnPressed.connect(self.handle_login)

        main_layout.addWidget(self.login_button)
        
        # Botão de Sair
        self.exit_button = QPushButton("Sair do Sistema")
        self.exit_button.setStyleSheet("background-color: #F44336; color: white;")
        self.exit_button.clicked.connect(self.close) # Fecha a aplicação
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
            # Abre o diálogo de cadastro de funcionário
            admin_dialog = CadastroFuncionarioDialog(self.db_connection)
            admin_dialog.setWindowTitle("Cadastro do Administrador Mestre")
            if admin_dialog.exec() != QDialog.Accepted:
                # Se o usuário não cadastrar o admin e cancelar, fecha o sistema
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

            # Comparação de Hashes (Segurança)
            if senha_hash_db == senha_hash_digitada:
                # Login bem-sucedido
                self.user_data = {
                    'id': id_db, 
                    'nome': nome_db, 
                    'login': login_db, 
                    'cargo': cargo_db
                }
                self.accept() # Aceita o diálogo e continua para a janela principal
            else:
                QMessageBox.critical(self, "Erro de Login", "Senha incorreta.")
        else:
            QMessageBox.critical(self, "Erro de Login", "Usuário não encontrado.")