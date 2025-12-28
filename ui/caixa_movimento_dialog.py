from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QTextEdit
)
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QDoubleValidator, QFont
from typing import Literal

# O tipo de movimento será estritamente 'Sangria' ou 'Suprimento'
MovimentoTipo = Literal['Sangria', 'Suprimento']

class CaixaMovimentoDialog(QDialog):
    
    def __init__(self, caixa_manager, id_caixa_aberto: int, id_funcionario: int, tipo: MovimentoTipo, parent=None):
        super().__init__(parent)
        
        self.caixa_manager = caixa_manager
        self.id_caixa_aberto = id_caixa_aberto
        self.id_funcionario = id_funcionario
        self.tipo = tipo  # 'Sangria' ou 'Suprimento'
        
        # Validação inicial
        if self.id_caixa_aberto <= 0:
            QMessageBox.critical(self, "Erro", "Nenhuma sessão de caixa aberta para realizar esta operação.")
            self.reject()
            return
            
        self.setWindowTitle(f"Caixa: {self.tipo}")
        self.resize(400, 300) 
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Título ---
        title_text = f"💰 Registrar {self.tipo}"
        title_label = QLabel(title_text)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # --- Formulário de Entrada ---
        form_layout = QFormLayout()
        
        # 1. Valor
        self.valor_input = QLineEdit() 
        self.valor_input.setPlaceholderText("0,00")
        self.valor_input.setFont(QFont("Arial", 12))
        
        # Configurar validador para aceitar apenas valores monetários
        validator = QDoubleValidator(0.01, 99999.99, 2)
        validator.setLocale(QLocale(QLocale.Portuguese, QLocale.Brazil)) 
        self.valor_input.setValidator(validator)
        
        form_layout.addRow(QLabel("Valor (R$):"), self.valor_input)
        
        # 2. Motivo
        self.motivo_input = QTextEdit()
        self.motivo_input.setFixedHeight(60)
        self.motivo_input.setPlaceholderText("Descreva o motivo da movimentação (Obrigatório)")
        
        form_layout.addRow(QLabel("Motivo:"), self.motivo_input)
        
        main_layout.addLayout(form_layout)
        
        # --- Botões ---
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        confirm_button = QPushButton(f"Confirmar {self.tipo}")
        confirm_button.setFont(QFont("Arial", 10, QFont.Bold))
        confirm_button.clicked.connect(self.handle_confirmar_movimento)
        confirm_button.setDefault(True)
        button_layout.addWidget(confirm_button)
        
        main_layout.addLayout(button_layout)
        
        # Foco inicial no campo de valor
        self.valor_input.setFocus()
        self.valor_input.selectAll()

    def get_valor_e_motivo(self) -> tuple[float, str]:
        """Retorna o valor como float e o motivo como string."""
        motivo = self.motivo_input.toPlainText().strip()
        try:
            # Substitui vírgula por ponto para conversão correta em Python
            text = self.valor_input.text().replace(',', '.')
            valor = float(text)
            return valor, motivo
        except ValueError:
            return 0.0, motivo

    def handle_confirmar_movimento(self):
        valor, motivo = self.get_valor_e_motivo()
        
        if valor <= 0:
            QMessageBox.warning(self, "Valor Inválido", "Por favor, insira um valor positivo.")
            self.valor_input.setFocus()
            return
        
        if not motivo:
            QMessageBox.warning(self, "Motivo Obrigatório", "É necessário descrever o motivo da movimentação.")
            self.motivo_input.setFocus()
            return
            
        # Confirmação final antes de registrar
        confirm = QMessageBox.question(
            self, 
            "Confirmação", 
            f"Deseja realmente registrar um(a) **{self.tipo}** de R$ **{valor:,.2f}**?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Chama a lógica de negócios
            success, message = self.caixa_manager.registrar_movimentacao(
                id_caixa=self.id_caixa_aberto,
                id_funcionario=self.id_funcionario,
                tipo=self.tipo,
                valor=valor,
                motivo=motivo
            )
            
            if success:
                QMessageBox.information(self, f"{self.tipo} Sucesso", message)
                self.accept() # Fecha o diálogo com sucesso
            else:
                QMessageBox.critical(self, f"Erro na {self.tipo}", message)

# FIM DO ARQUIVO ui/caixa_movimento_dialog.py