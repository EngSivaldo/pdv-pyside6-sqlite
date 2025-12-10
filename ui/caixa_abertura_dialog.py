# Arquivo: ui/caixa_abertura_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QDoubleValidator, QFont
# Importa o CaixaManager, embora não o instanciemos aqui, é bom para referência de tipos
from core.caixa_manager import CaixaManager 

class CaixaAberturaDialog(QDialog):
    
    # CORREÇÃO: Recebe o objeto caixa_manager pronto da PDVWindow
    def __init__(self, caixa_manager, id_funcionario_logado: int, nome_funcionario: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abertura de Caixa")
        # Removido setFixedSize para melhor adaptação, mas mantido um tamanho se necessário
        self.resize(400, 200) 
        
        # Armazena o Gerenciador de Caixa
        self.caixa_manager = caixa_manager
        self.id_funcionario_logado = id_funcionario_logado
        self.nome_funcionario = nome_funcionario
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Título e Informação ---
        title_label = QLabel("💰 Iniciar Sessão de Caixa")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Usando Markdown para negrito no QLabel
        info_label = QLabel(f"Vendedor: <b>{self.nome_funcionario}</b><br/>Insira o valor do Fundo de Troco.")
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)
        
        # --- Campo de Valor ---
        valor_layout = QHBoxLayout()
        valor_layout.addWidget(QLabel("Valor Inicial (R$):"))
        
        self.valor_input = QLineEdit()
        self.valor_input.setPlaceholderText("Ex: 50,00")
        self.valor_input.setFont(QFont("Arial", 12))
        
        # Configurar validador para aceitar apenas números (Reais)
        validator = QDoubleValidator(0.00, 99999.99, 2)
        validator.setLocale(QLocale(QLocale.Portuguese, QLocale.Brazil)) 
        self.valor_input.setValidator(validator)
        
        self.valor_input.setText("100,00") 
        self.valor_input.selectAll()
        
        valor_layout.addWidget(self.valor_input)
        main_layout.addLayout(valor_layout)
        
        # --- Botões ---
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        open_button = QPushButton("Abrir Caixa")
        open_button.setFont(QFont("Arial", 10, QFont.Bold))
        open_button.clicked.connect(self.handle_abrir_caixa)
        open_button.setDefault(True) 
        button_layout.addWidget(open_button)
        
        main_layout.addLayout(button_layout)
        
    def get_valor_abertura(self):
        """Retorna o valor de abertura como float."""
        try:
            # Substitui vírgula por ponto para conversão correta em Python/SQLite
            text = self.valor_input.text().replace(',', '.')
            return float(text)
        except ValueError:
            return 0.0

    def handle_abrir_caixa(self):
        valor = self.get_valor_abertura()
        
        if valor <= 0:
            QMessageBox.warning(self, "Valor Inválido", "O fundo de troco deve ser um valor positivo.")
            self.valor_input.setFocus()
            return
            
        # CORREÇÃO: Usa o self.caixa_manager já existente
        # Removemos a linha: caixa_manager = CaixaManager(self.db_connection)
        
        # Tenta Abrir o Caixa
        success = self.caixa_manager.abrir_caixa(self.id_funcionario_logado, valor)
        
        if success:
            QMessageBox.information(self, "Sucesso", f"Caixa aberto com Fundo de Troco de R$ {self.valor_input.text()}!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro na Abertura", 
                                 "Não foi possível abrir o caixa. Verifique se já não existe outro caixa aberto para este usuário.")