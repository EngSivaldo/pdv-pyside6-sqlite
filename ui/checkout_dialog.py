from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QWidget, QMessageBox, QTableView, QHeaderView, 
    QDoubleSpinBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont
from typing import List, Dict, Any

# ====================================================================
# MODELO DE DADOS PARA PAGAMENTOS MISTOS
# ====================================================================

class PaymentTableModel(QAbstractTableModel):
    """Modelo de dados para exibir e gerenciar a lista de pagamentos."""
    
    def __init__(self, payments: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.payments = payments
        self.headers = ["Método", "Valor (R$)"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.payments)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:
                return self.payments[row]["method"]
            elif col == 1:
                # Formata o valor como moeda
                return self._format_currency_display(self.payments[row]['value'])
        
        if role == Qt.TextAlignmentRole:
            if col == 1:
                return int(Qt.AlignRight | Qt.AlignVCenter)
        
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None
        
    def add_payment(self, method: str, value: float):
        """Adiciona um pagamento à lista e notifica a view."""
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.payments.append({"method": method, "value": value})
        self.endInsertRows()
        
    def get_total_paid(self):
        """Retorna a soma de todos os valores pagos registrados."""
        return sum(item['value'] for item in self.payments)

    def _format_currency_display(self, value: float) -> str:
        """Formata um valor float para string de moeda brasileira."""
        # Note: Esta função é duplicada do CheckoutDialog, mas é necessária aqui para o QAbstractTableModel
        return f"{value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

# ====================================================================
# CLASSE PRINCIPAL: CHECKOUT DIALOG
# ====================================================================

class CheckoutDialog(QDialog):
    """Diálogo completo para gestão de pagamentos mistos, desconto e troco."""

    def __init__(self, subtotal_bruto: float, total_liquido: float, total_discount_value: float, total_service_fee: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💵 Finalizar Pagamento (Pagamento Misto)")
        self.setGeometry(300, 300, 700, 550) 
        
        self.subtotal_bruto = subtotal_bruto
        self.total_liquido = total_liquido # Este é o valor final a ser pago
        self.total_discount_value = total_discount_value
        self.total_service_fee = total_service_fee
        
        # Variáveis que serão lidas pela PDVWindow
        self.troco = 0.0 # Valor real do troco (só de dinheiro)
        self.valor_recebido = 0.0 # Total de todos os pagamentos
        
        self.payments_list = []
        self.payment_model = PaymentTableModel(self.payments_list)
        
        self._setup_ui()
        self._apply_style() 
        self.update_restante_and_troco() # Inicializa o display

    def _setup_ui(self):
        main_layout = QHBoxLayout(self) # Layout principal horizontal
        
        # --- PAINEL ESQUERDO: Pagamentos e Ações (60%) ---
        payment_panel = QWidget()
        payment_layout = QVBoxLayout(payment_panel)
        
        # 1. Tabela de Pagamentos
        payment_layout.addWidget(QLabel("MÉTODOS DE PAGAMENTO REGISTRADOS:"))
        self.payment_table_view = QTableView()
        self.payment_table_view.setModel(self.payment_model)
        self.payment_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        payment_layout.addWidget(self.payment_table_view)

        # 2. Input para Novo Pagamento
        input_payment_layout = QHBoxLayout()
        self.new_payment_value_input = QDoubleSpinBox()
        self.new_payment_value_input.setRange(0.0, 99999.99)
        self.new_payment_value_input.setPrefix("R$ ")
        input_payment_layout.addWidget(self.new_payment_value_input)

        self.add_cash_btn = QPushButton("Dinheiro (F9)")
        self.add_cash_btn.clicked.connect(lambda: self._add_payment_from_input("Dinheiro"))
        
        self.add_credit_btn = QPushButton("Crédito (F10)")
        self.add_credit_btn.clicked.connect(lambda: self._add_payment_from_input("Cartão Crédito"))
        
        input_payment_layout.addWidget(self.add_cash_btn)
        input_payment_layout.addWidget(self.add_credit_btn)
        
        payment_layout.addLayout(input_payment_layout)
        
        # 3. Botão Remover Pagamento
        self.remove_payment_btn = QPushButton("Remover Último Pagamento")
        self.remove_payment_btn.clicked.connect(self._remove_last_payment)
        payment_layout.addWidget(self.remove_payment_btn)
        
        # 4. Botões de Confirmação/Cancelamento
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar (ESC)")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("Confirmar (Enter)")
        confirm_btn.clicked.connect(self.confirm_and_accept)
        confirm_btn.setObjectName("confirmCheckoutButton")
        button_layout.addWidget(confirm_btn)
        
        payment_layout.addLayout(button_layout)
        
        main_layout.addWidget(payment_panel, 3)

        # --- PAINEL DIREITO: Totais e Resumo (40%) ---
        summary_panel = QWidget()
        summary_layout = QVBoxLayout(summary_panel)
        
        # 1. Detalhes (NOVOS)
        summary_layout.addWidget(QLabel("DETALHES DA VENDA:"))
        
        summary_layout.addWidget(self._create_summary_label("Subtotal Bruto:", self.subtotal_bruto))
        summary_layout.addWidget(self._create_summary_label("(-) Desconto Total:", self.total_discount_value, is_negative=True))
        summary_layout.addWidget(self._create_summary_label("(+) Taxa Serviço:", self.total_service_fee))
        
        summary_layout.addWidget(QLabel("-" * 25))
        
        # 2. Total Líquido (A Pagar)
        total_label = QLabel("TOTAL LÍQUIDO A PAGAR:")
        total_label.setFont(QFont("Arial", 12))
        summary_layout.addWidget(total_label)
        
        self.total_display = QLabel(self._format_currency(self.total_liquido))
        self.total_display.setObjectName("checkoutTotalDisplay")
        summary_layout.addWidget(self.total_display)
        
        summary_layout.addSpacing(20)

        # 3. Restante a Pagar / Troco
        summary_layout.addWidget(QLabel("PAGO / RESTANTE / TROCO:"))
        self.troco_display = QLabel("R$ 0,00")
        self.troco_display.setObjectName("trocoDisplay")
        summary_layout.addWidget(self.troco_display)

        summary_layout.addStretch(1) # Empurra o conteúdo para cima
        
        main_layout.addWidget(summary_panel, 2)
        
        # Atalhos de Foco: Coloca o foco no input do valor de pagamento
        self.new_payment_value_input.setFocus()
        
    def _create_summary_label(self, title: str, value: float, is_negative: bool = False) -> QWidget:
        """Cria um widget QHBoxLayout para exibir detalhes formatados."""
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        value_label = QLabel(self._format_currency(value))
        value_label.setAlignment(Qt.AlignRight)
        
        if is_negative and value > 0:
             value_label.setStyleSheet("color: #bf616a;") # Nord Red para negativo
        
        h_layout.addWidget(title_label)
        h_layout.addWidget(value_label)
        return container
        
    def _apply_style(self):
        """Aplica o estilo visual do QSS do pai."""
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())

    def _format_currency(self, value: float) -> str:
        """Formata um valor float para string de moeda brasileira."""
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    # ==================== LÓGICA DE PAGAMENTO ====================
    
    def get_total_cash_paid(self):
        """Retorna a soma dos valores pagos especificamente em dinheiro."""
        return sum(item['value'] for item in self.payments_list if item['method'] == 'Dinheiro')

    def _add_payment_from_input(self, method: str):
        """Adiciona um pagamento usando o valor do QDoubleSpinBox."""
        value = self.new_payment_value_input.value()
        
        if value <= 0:
            QMessageBox.warning(self, "Aviso", "O valor do pagamento deve ser maior que zero.")
            return

        self.payment_model.add_payment(method, value)
        self.update_restante_and_troco()
        
        # Limpa e foca no input
        self.new_payment_value_input.setValue(0.0)
        self.new_payment_value_input.setFocus()

    def _remove_last_payment(self):
        """Remove o último pagamento da lista."""
        if not self.payments_list:
            return
            
        self.payment_model.beginRemoveRows(QModelIndex(), len(self.payments_list) - 1, len(self.payments_list) - 1)
        self.payments_list.pop()
        self.payment_model.endRemoveRows()
        
        self.update_restante_and_troco()

    def update_restante_and_troco(self):
        """
        Calcula o total pago e determina o valor restante ou o troco.
        
        CORREÇÃO: O troco é calculado APENAS a partir do Dinheiro pago.
        """
        
        total_paid = self.payment_model.get_total_paid()
        total_cash = self.get_total_cash_paid() # Dinheiro total recebido
        
        # 1. FALTA PAGAR
        if total_paid < self.total_liquido:
            restante = self.total_liquido - total_paid
            self.troco = 0.0 # Troco é zero
            
            self.troco_display.setText(f"FALTA: {self._format_currency(restante)}")
            self.troco_display.setStyleSheet("color: #bf616a;") # Nord Red (Alerta)
            
            # Ajusta o range do input para o restante (ou mais um pouco)
            self.new_payment_value_input.setRange(0.0, restante + 100.0) 
            
        # 2. PAGO SUFICIENTEMENTE (Total Pago >= Total Líquido)
        else:
            # Valor que excedeu o total líquido
            excedente_total = total_paid - self.total_liquido 
            
            # ⭐️ TROCO CORRIGIDO: O troco é o excedente, limitado ao Dinheiro recebido. ⭐️
            self.troco = min(total_cash, excedente_total)
            
            if self.troco > 0:
                self.troco_display.setText(f"TROCO: {self._format_currency(self.troco)}")
                self.troco_display.setStyleSheet("color: #88c0d0;") # Nord Cyan (Sucesso)
            else:
                self.troco_display.setText(f"PAGO TOTAL: {self._format_currency(total_paid)}")
                self.troco_display.setStyleSheet("color: #a3be8c;") # Nord Green (Pago exato ou excedente em cartão/pix)
                
            self.new_payment_value_input.setRange(0.0, 99999.99) # Range grande novamente

    def confirm_and_accept(self):
        """Valida se o total pago é suficiente e aceita a confirmação da venda."""
        self.update_restante_and_troco() # Garante o cálculo final

        # Não é permitido aceitar se ainda falta pagar
        if self.troco < 0: # self.troco é negativo apenas se total_paid < total_liquido (cenário "FALTA")
            QMessageBox.critical(self, "Valor Insuficiente", 
                                 f"O total pago é menor que o valor líquido. Faltam {self._format_currency(abs(self.troco))}")
            self.new_payment_value_input.setFocus()
            return
            
        # Se pagou o suficiente, salvamos o total recebido e aceitamos.
        self.valor_recebido = self.payment_model.get_total_paid()
        self.accept() 

    # ui/checkout_dialog.py (Substitua todo o método keyPressEvent)

    def keyPressEvent(self, event):
        """Atalhos de teclado: Enter, Escape, F9 (Dinheiro), F10 (Crédito)."""
        
        # Verifica se há algum valor digitado no SpinBox.
        input_value = self.new_payment_value_input.value()
        
        # 1. TRATAMENTO DO ENTER (Confirmação)
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Se houver um valor no input, adicione-o como Dinheiro antes de confirmar
            # Isso atende à expectativa do usuário que digitou um valor e apertou Enter/Return.
            if input_value > 0:
                self._add_payment_from_input("Dinheiro")
            
            self.confirm_and_accept()
            
        # 2. TRATAMENTO DO ESCAPE (Cancelamento)
        elif event.key() == Qt.Key_Escape:
            self.reject()
            
        # 3. TRATAMENTO DO F9 (Dinheiro)
        elif event.key() == Qt.Key_F9:
            # Se o campo de input já tem um valor, usa esse valor para o pagamento em Dinheiro.
            if input_value > 0.0:
                self._add_payment_from_input("Dinheiro")
            else:
                # Caso contrário, calcula o restante e usa esse valor (função "Pagar Total")
                total_paid = self.payment_model.get_total_paid()
                restante_a_pagar = self.total_liquido - total_paid
                
                # Se faltar pagar, seta o valor e adiciona
                if restante_a_pagar > 0:
                    self.new_payment_value_input.setValue(restante_a_pagar)
                    self._add_payment_from_input("Dinheiro")
                else:
                    # Se já está pago, apenas adiciona o que está no input (que deve ser 0.0)
                    self._add_payment_from_input("Dinheiro")


        # 4. TRATAMENTO DO F10 (Crédito)
        elif event.key() == Qt.Key_F10:
            # Mesma lógica que F9, mas para Crédito.
            if input_value > 0.0:
                self._add_payment_from_input("Cartão Crédito")
            else:
                total_paid = self.payment_model.get_total_paid()
                restante_a_pagar = self.total_liquido - total_paid
                
                if restante_a_pagar > 0:
                    self.new_payment_value_input.setValue(restante_a_pagar)
                    self._add_payment_from_input("Cartão Crédito")
                else:
                    self._add_payment_from_input("Cartão Crédito")
                    
        else:
            super().keyPressEvent(event)