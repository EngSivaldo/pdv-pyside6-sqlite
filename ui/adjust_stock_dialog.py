# ui/adjust_stock_dialog.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QMessageBox
from PySide6.QtCore import Qt

class AdjustStockDialog(QDialog):
    """Diálogo para ajustar (adicionar ou remover) estoque de um produto."""
    
    def __init__(self, product_name, current_qty, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ajustar Estoque: {product_name}")
        self.current_qty = current_qty
        self.new_adjustment = 0.0
        
        self.setup_ui(product_name)

    def setup_ui(self, product_name):
        main_layout = QVBoxLayout(self)
        
        main_layout.addWidget(QLabel(f"Produto: **{product_name}**"))
        main_layout.addWidget(QLabel(f"Estoque Atual: **{self.current_qty:,.2f}**"))
        
        # Campo para o ajuste (adição ou subtração)
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Adicionar/Remover Quantidade:"))
        
        self.adjustment_input = QDoubleSpinBox()
        self.adjustment_input.setDecimals(2)
        # Permite valores negativos (remoção) e positivos (adição)
        self.adjustment_input.setRange(-99999.99, 99999.99) 
        self.adjustment_input.setValue(0.00)
        
        qty_layout.addWidget(self.adjustment_input)
        main_layout.addLayout(qty_layout)
        
        # Botões
        button_layout = QHBoxLayout()
        save_button = QPushButton("✅ Aplicar Ajuste")
        save_button.clicked.connect(self.accept_adjustment)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def accept_adjustment(self):
        """Valida e aceita o ajuste, retornando o valor."""
        self.new_adjustment = self.adjustment_input.value()
        
        # Verifica se o ajuste negativo é maior que o estoque atual
        if self.new_adjustment < 0 and abs(self.new_adjustment) > self.current_qty:
            QMessageBox.critical(self, "Erro de Estoque", 
                                 "Não é possível remover mais produtos do que o estoque atual.")
            return

        self.accept()

    def get_adjustment(self):
        return self.new_adjustment