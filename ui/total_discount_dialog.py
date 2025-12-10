# ui/total_discount_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class TotalDiscountDialog(QDialog):
    """
    Diálogo para aplicação de desconto ou acréscimo total (taxa de serviço)
    sobre o subtotal da venda.
    """

    def __init__(self, subtotal_bruto: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏷️ Aplicar Desconto/Taxa")
        self.setGeometry(300, 300, 350, 200)
        
        self.subtotal_bruto = subtotal_bruto
        # Valores que serão retornados após aceitar:
        self.final_discount_value = 0.0 # Valor absoluto do desconto (R$)
        self.final_service_fee = 0.0    # Valor absoluto da taxa (R$)

        self._setup_ui()
        self._calculate_and_update() # Inicializa o cálculo

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 1. Display do Subtotal
        main_layout.addWidget(QLabel(f"Subtotal Bruto: {self._format_currency(self.subtotal_bruto)}"))

        # 2. Input de Desconto (%)
        main_layout.addWidget(QLabel("Desconto Total (%)"))
        self.discount_percent_input = QLineEdit("0")
        self.discount_percent_input.setAlignment(Qt.AlignRight)
        self.discount_percent_input.textChanged.connect(self._calculate_and_update)
        main_layout.addWidget(self.discount_percent_input)
        
        # 3. Input de Taxa de Serviço (%)
        main_layout.addWidget(QLabel("Taxa de Serviço (%)"))
        self.fee_percent_input = QLineEdit("0")
        self.fee_percent_input.setAlignment(Qt.AlignRight)
        self.fee_percent_input.textChanged.connect(self._calculate_and_update)
        main_layout.addWidget(self.fee_percent_input)

        # 4. Display do Total Líquido (Resultado)
        main_layout.addWidget(QLabel("-" * 25))
        main_layout.addWidget(QLabel("TOTAL LÍQUIDO:"))
        self.final_total_display = QLabel(self._format_currency(self.subtotal_bruto))
        self.final_total_display.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(self.final_total_display)
        
        # 5. Botões
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject) 
        confirm_btn = QPushButton("Aplicar")
        confirm_btn.clicked.connect(self._confirm_and_accept)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        main_layout.addLayout(button_layout)
        
        self.discount_percent_input.setFocus()

    def _format_currency(self, value: float) -> str:
        """Formata um valor float para string de moeda brasileira."""
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    def _calculate_and_update(self):
        """Calcula o desconto/taxa e atualiza o display do total líquido."""
        try:
            # Converte e garante que são floats (aceita vírgula)
            discount_percent = float(self.discount_percent_input.text().replace(',', '.') or 0.0)
            fee_percent = float(self.fee_percent_input.text().replace(',', '.') or 0.0)
            
            # Cálculo dos valores em R$
            discount_value = self.subtotal_bruto * (discount_percent / 100)
            fee_value = self.subtotal_bruto * (fee_percent / 100)
            
            # Cálculo do Total Líquido
            total_liquido = self.subtotal_bruto - discount_value + fee_value
            
            # Armazena os valores finais para retorno
            self.final_discount_value = discount_value
            self.final_service_fee = fee_value
            self.total_liquido = total_liquido
            
            # Atualiza o display
            self.final_total_display.setText(self._format_currency(total_liquido))
            
        except ValueError:
            self.final_total_display.setText("R$ ERRO")
            self.final_discount_value = 0.0
            self.final_service_fee = 0.0

    def _confirm_and_accept(self):
        """Valida e aceita a aplicação dos valores."""
        self._calculate_and_update() # Garante o cálculo final
        
        if self.total_liquido < 0:
             QMessageBox.critical(self, "Valor Inválido", "O total líquido não pode ser negativo após descontos.")
             return
             
        self.accept()