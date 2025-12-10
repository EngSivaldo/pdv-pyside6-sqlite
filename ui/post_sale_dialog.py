from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont  # ⭐️ ADICIONE ESTA LINHA ⭐️
# Opcional: Remova o import de QFont no _setup_ui, se existir, e use QFont.Bold
# ou importe QFont e QFont.Weight
from PySide6.QtGui import QFont, QFont, QFont

class PostSaleDialog(QDialog):
    """
    Diálogo exibido após a finalização de uma venda para confirmar
    a impressão de recibo, nota fiscal ou fechar.
    """
    
    # Constantes para os resultados (para facilitar a leitura no main_window)
    PRINT_RECEIPT = 1
    PRINT_INVOICE = 2
    NO_ACTION = 0 # Fechar

    def __init__(self, sale_id: int, total_pago: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✅ Venda Concluída")
        self.setGeometry(400, 400, 350, 200)
        self.setModal(True)
        
        self.sale_id = sale_id
        
        # ⚠️ O resultado é armazenado aqui antes de fechar o diálogo.
        self.result_action = self.NO_ACTION 
        
        self._setup_ui(total_pago)
        
    def _setup_ui(self, total_pago: float):
        main_layout = QVBoxLayout(self)
        
        # Mensagem de Sucesso
        msg_label = QLabel(f"Venda #{self.sale_id} finalizada com sucesso!")
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setFont(QFont("Arial", 11, QFont.Bold))
        main_layout.addWidget(msg_label)
        
        total_label = QLabel(f"Total Pago: {self._format_currency(total_pago)}")
        total_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(total_label)
        
        main_layout.addWidget(QLabel("O que deseja fazer agora?"))
        
        # Botões de Opção
        button_layout = QHBoxLayout()
        
        # Botão 1: Recibo Simples
        self.receipt_btn = QPushButton("Imprimir Recibo")
        self.receipt_btn.clicked.connect(self._handle_receipt)
        button_layout.addWidget(self.receipt_btn)
        
        # Botão 2: Nota Fiscal (Mais complexa, requer dados do cliente)
        self.invoice_btn = QPushButton("Emitir NF (Exigido)")
        self.invoice_btn.clicked.connect(self._handle_invoice)
        button_layout.addWidget(self.invoice_btn)
        
        # Botão 3: Fechar (Ação padrão)
        close_btn = QPushButton("Fechar/Nova Venda (ESC)")
        close_btn.clicked.connect(self.close) # Apenas fecha
        
        main_layout.addLayout(button_layout)
        main_layout.addWidget(close_btn)
        
        self.receipt_btn.setFocus()

    def _format_currency(self, value: float) -> str:
        """Formata um valor float para string de moeda brasileira."""
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    def _handle_receipt(self):
        """Define a ação como Recibo e fecha com aceitação."""
        self.result_action = self.PRINT_RECEIPT
        self.accept()
        
    def _handle_invoice(self):
        """Define a ação como Nota Fiscal e fecha com aceitação."""
        self.result_action = self.PRINT_INVOICE
        self.accept()
        
    def close(self):
        """Define a ação como Nenhuma e fecha com rejeição (mas é ok, pois result_action é 0)."""
        self.result_action = self.NO_ACTION
        self.reject()

    def keyPressEvent(self, event):
        """Atalhos para facilitar."""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_1: # Exemplo: Tecla 1 para recibo
            self._handle_receipt()
        elif event.key() == Qt.Key_2: # Exemplo: Tecla 2 para NF
            self._handle_invoice()
        else:
            super().keyPressEvent(event)