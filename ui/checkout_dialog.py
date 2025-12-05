# ui/checkout_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class CheckoutDialog(QDialog):
    """Diálogo para confirmação de venda, valor recebido e cálculo do troco."""

    def __init__(self, total_venda: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💵 Finalizar Pagamento")
        self.setGeometry(300, 300, 400, 300)
        
        self.total_venda = total_venda
        self.valor_recebido = 0.0
        self.troco = 0.0

        self._setup_ui()
        self._apply_style() # Aplicaremos o estilo aqui
        self.received_input.setFocus()
        self.update_troco() # Inicializa o troco

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- 1. Display do Total ---
        total_label = QLabel("TOTAL A PAGAR:")
        total_label.setFont(QFont("Arial", 12))
        main_layout.addWidget(total_label)

        self.total_display = QLabel(self._format_currency(self.total_venda))
        self.total_display.setObjectName("checkoutTotalDisplay")
        self.total_display.setFont(QFont("Arial", 28, QFont.Bold))
        self.total_display.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.total_display)
        
        # --- 2. Input de Valor Recebido ---
        received_layout = QHBoxLayout()
        received_layout.addWidget(QLabel("VALOR RECEBIDO:"))
        self.received_input = QLineEdit("0.00")
        self.received_input.setAlignment(Qt.AlignRight)
        self.received_input.setFont(QFont("Arial", 16))
        self.received_input.textChanged.connect(self.update_troco)
        received_layout.addWidget(self.received_input)
        main_layout.addLayout(received_layout)

        # --- 3. Display do Troco ---
        troco_layout = QHBoxLayout()
        troco_layout.addWidget(QLabel("TROCO:"))
        self.troco_display = QLabel("R$ 0,00")
        self.troco_display.setObjectName("trocoDisplay")
        self.troco_display.setFont(QFont("Arial", 18, QFont.Bold))
        self.troco_display.setAlignment(Qt.AlignRight)
        troco_layout.addWidget(self.troco_display)
        main_layout.addLayout(troco_layout)
        
        main_layout.addSpacing(20)

        # --- 4. Botões de Ação ---
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar (ESC)")
        cancel_btn.clicked.connect(self.reject) # QDialog.reject fecha o diálogo com código de rejeição
        button_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("Confirmar (Enter)")
        confirm_btn.clicked.connect(self.confirm_and_accept)
        confirm_btn.setObjectName("confirmCheckoutButton")
        button_layout.addWidget(confirm_btn)
        
        main_layout.addLayout(button_layout)

    def _apply_style(self):
        """Aplica o estilo visual do QSS, se disponível."""
        # Se você tiver o styles.qss na raiz, esta função garantirá que o estilo seja aplicado
        # ao novo diálogo, mantendo a consistência do tema.
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())
        
        # Estilos manuais de destaque para o Checkout, caso o QSS falhe ou não seja aplicado:
        self.total_display.setStyleSheet("color: #a3be8c;") # Verde
        self.troco_display.setStyleSheet("color: #88c0d0;") # Azul
        
    def _format_currency(self, value: float) -> str:
        """Formata um valor float para string de moeda brasileira."""
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    def update_troco(self):
        """Calcula e atualiza o valor do troco exibido."""
        try:
            # Substitui vírgula por ponto para conversão
            received_text = self.received_input.text().replace(',', '.').strip()
            self.valor_recebido = float(received_text)
        except ValueError:
            self.valor_recebido = 0.0
        
        self.troco = self.valor_recebido - self.total_venda
        
        # Destaca o troco negativo em vermelho
        if self.troco < 0:
            self.troco_display.setText(f"FALTAM {self._format_currency(abs(self.troco))}")
            self.troco_display.setStyleSheet("color: #bf616a;") # Nord Red
        else:
            self.troco_display.setText(self._format_currency(self.troco))
            self.troco_display.setStyleSheet("color: #88c0d0;") # Nord Cyan

    def confirm_and_accept(self):
        """Valida e aceita a confirmação da venda."""
        self.update_troco() # Garante o cálculo final

        if self.valor_recebido < self.total_venda:
            QMessageBox.critical(self, "Valor Insuficiente", 
                                 f"O valor recebido é menor que o total da venda. Faltam {self._format_currency(abs(self.troco))}")
            self.received_input.setFocus()
            return

        # QDialog.accept fecha o diálogo com código de aceitação
        self.accept() 

    def keyPressEvent(self, event):
        """Atalhos de teclado: Enter para confirmar e Escape para cancelar."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.confirm_and_accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

# --- Exemplo de uso (Para teste) ---
# if __name__ == '__main__':
#     from PySide6.QtWidgets import QApplication
#     app = QApplication([])
#     dialog = CheckoutDialog(total_venda=150.75)
#     if dialog.exec() == QDialog.Accepted:
#         print(f"Venda Aceita. Total: {dialog.total_venda}, Recebido: {dialog.valor_recebido}, Troco: {dialog.troco}")
#     else:
#         print("Venda Cancelada.")
#     app.exec()