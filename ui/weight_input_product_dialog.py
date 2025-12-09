# CÓDIGO CORRIGIDO
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QDoubleSpinBox, QPushButton
)
from PySide6.QtGui import QFont # ✅ QFont deve ser importado de QtGui
from PySide6.QtCore import Qt
# ...
from PySide6.QtCore import Qt

class WeightInputProductDialog(QDialog):
    """
    Diálogo para permitir que o caixa insira a quantidade (peso) 
    para produtos vendidos a granel.
    """

    def __init__(self, product_name: str, product_price: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Entrada de Peso: {product_name}")
        self.setGeometry(400, 400, 350, 200) # Tamanho compacto
        
        self.product_name = product_name
        self.product_price = product_price
        self.weight_qty = 0.0 # Peso final
        self.total_value = 0.0 # Valor total calculado
        
        self.setup_ui()
        self.update_total() # Inicializa o cálculo

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        input_font = QFont("Arial", 14)
        
        # 1. Informações do Produto
        main_layout.addWidget(QLabel(f"Produto: **{self.product_name}**"))
        price_label = QLabel(f"Preço por KG: R$ {self.product_price:,.2f}")
        price_label.setStyleSheet("color: #4caf50; font-weight: bold;") # Verde de preço
        main_layout.addWidget(price_label)
        
        # 2. Entrada de Peso
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("Peso (KG):"))
        
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setDecimals(3) # Três casas decimais para peso
        self.weight_input.setRange(0.001, 999.000)
        self.weight_input.setValue(0.100) # Valor inicial sugerido (100g)
        self.weight_input.setSingleStep(0.050) # Incremento de 50g
        self.weight_input.setFont(input_font)
        self.weight_input.setAlignment(Qt.AlignRight)
        self.weight_input.valueChanged.connect(self.update_total)
        
        weight_layout.addWidget(self.weight_input)
        main_layout.addLayout(weight_layout)
        
        # 3. Display do Total Calculado
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("TOTAL (R$):"))
        
        self.total_display = QLabel("R$ 0,00")
        self.total_display.setFont(QFont("Arial", 16, QFont.Bold))
        self.total_display.setAlignment(Qt.AlignRight)
        total_layout.addWidget(self.total_display)
        main_layout.addLayout(total_layout)
        
        main_layout.addSpacing(10)
        
        # 4. Botões de Ação
        button_layout = QHBoxLayout()
        confirm_btn = QPushButton("Adicionar (Enter)")
        confirm_btn.setStyleSheet("background-color: #4caf50; color: white;")
        confirm_btn.clicked.connect(self.accept_weight)
        
        cancel_btn = QPushButton("Cancelar (ESC)")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

    def update_total(self):
        """Calcula e atualiza o valor total da venda baseada no peso."""
        self.weight_qty = self.weight_input.value()
        self.total_value = self.weight_qty * self.product_price
        
        # Formata para R$ BRL
        formatted_total = f"R$ {self.total_value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        self.total_display.setText(formatted_total)

    def accept_weight(self):
        """Valida e aceita o peso para adicionar ao carrinho."""
        if self.weight_qty <= 0:
            QMessageBox.warning(self, "Aviso", "O peso deve ser maior que zero.")
            self.weight_input.setFocus()
            return
        self.accept()
        
    def get_weight_and_total(self) -> tuple[float, float]:
        """Retorna a quantidade (peso) e o valor total calculado."""
        return self.weight_qty, self.total_value
        
    def keyPressEvent(self, event):
        """Atalhos de teclado: Enter para confirmar e Escape para cancelar."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept_weight()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)