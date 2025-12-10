# Arquivo: ui/pagamento_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QComboBox, QFormLayout, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QFont

class PagamentoDialog(QDialog):
    
    def __init__(self, total_venda: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Finalizar Venda - Pagamento")
        self.setFixedSize(500, 400)
        
        self.total_venda = total_venda
        self.troco = 0.0
        self.valor_recebido = 0.0
        self.pagamentos = []  # Lista de dicionários: [{'metodo': 'Dinheiro', 'valor': 100.00}]
        
        self.setup_ui()
        self.connect_signals()
        self._update_troco_display()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- 1. Total a Pagar (Display Grande) ---
        total_group = QVBoxLayout()
        label_title = QLabel("Total a Pagar")
        label_title.setAlignment(Qt.AlignCenter)
        label_title.setFont(QFont("Arial", 14))
        total_group.addWidget(label_title)
        
        self.label_total = QLabel(self._format_currency(self.total_venda))
        self.label_total.setFont(QFont("Arial", 30, QFont.Bold))
        self.label_total.setStyleSheet("color: white; background-color: #C0392B; padding: 10px; border-radius: 5px;")
        self.label_total.setAlignment(Qt.AlignCenter)
        total_group.addWidget(self.label_total)
        main_layout.addLayout(total_group)
        
        # --- 2. Área de Pagamento ---
        pagamento_area = QFormLayout()
        
        # Campo Valor Recebido (Input)
        self.input_recebido = QLineEdit()
        self.input_recebido.setPlaceholderText("0,00")
        self.input_recebido.setFont(QFont("Arial", 14))
        pagamento_area.addRow("Valor Recebido (R$):", self.input_recebido)
        
        # Seletor de Método
        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems(["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"])
        pagamento_area.addRow("Método:", self.combo_metodo)
        
        # Botão Adicionar Pagamento (Útil para pagamentos mistos)
        self.btn_adicionar = QPushButton("Adicionar Pagamento")
        self.btn_adicionar.setMinimumHeight(30)
        pagamento_area.addRow(self.btn_adicionar)
        
        main_layout.addLayout(pagamento_area)
        
        # --- 3. Display de Troco ---
        troco_group = QHBoxLayout()
        troco_group.addWidget(QLabel("Troco:"))
        self.label_troco = QLabel("R$ 0,00")
        self.label_troco.setFont(QFont("Arial", 20, QFont.Bold))
        self.label_troco.setStyleSheet("color: #2ECC71;")
        troco_group.addWidget(self.label_troco)
        troco_group.addStretch()
        main_layout.addLayout(troco_group)
        
        # --- 4. Botões de Ação ---
        btn_layout = QHBoxLayout()
        self.btn_confirmar = QPushButton("Confirmar Venda (Enter)")
        self.btn_confirmar.setMinimumHeight(40)
        self.btn_confirmar.setEnabled(False) # Começa desabilitado
        
        btn_cancelar = QPushButton("Cancelar (Esc)")
        btn_cancelar.setMinimumHeight(40)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(self.btn_confirmar)
        main_layout.addLayout(btn_layout)
        
    def connect_signals(self):
        self.input_recebido.textChanged.connect(self._recalcular)
        self.btn_confirmar.clicked.connect(self._confirmar_pagamento)
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_adicionar.clicked.connect(self._adicionar_pagamento)
        
    def _format_currency(self, value: float) -> str:
        """Formata um float para string de moeda brasileira."""
        locale = QLocale(QLocale.Portuguese, QLocale.Brazil)
        return locale.toString(value, 'f', 2)

    def _unformat_currency(self, text: str) -> float:
        """Converte string de moeda (virgula) para float (ponto)."""
        text = text.replace('.', '').replace(',', '.')
        try:
            return float(text)
        except ValueError:
            return 0.0

    def _adicionar_pagamento(self):
        """Adiciona o valor recebido e o método à lista de pagamentos."""
        valor = self._unformat_currency(self.input_recebido.text())
        metodo = self.combo_metodo.currentText()
        
        if valor <= 0:
            QMessageBox.warning(self, "Valor Inválido", "O valor de pagamento deve ser maior que zero.")
            return
            
        # Adiciona o pagamento
        self.pagamentos.append({'metodo': metodo, 'valor': valor})
        self.valor_recebido += valor
        
        # Atualiza o total a pagar (Para o fluxo de pagamento misto)
        # Se for pagamento misto, o total_venda real não muda, mas a lógica de troco deve considerar o acumulado.
        
        self._recalcular()
        
        # Limpa o input e desabilita a adição se a dívida for quitada
        if self.valor_recebido >= self.total_venda:
            self.input_recebido.setText(self._format_currency(self.valor_recebido - self.total_venda)) # Exibe o troco como sugestão
            self.btn_adicionar.setEnabled(False)
        else:
            self.input_recebido.clear()
            QMessageBox.information(self, "Pagamento Adicionado", f"R$ {self._format_currency(valor)} em {metodo} adicionado. Faltam R$ {self._format_currency(self.total_venda - self.valor_recebido):.2f}")


    def _recalcular(self):
        """Recalcula o troco com base no valor recebido no input + pagamentos já adicionados."""
        
        # Se já houver pagamentos adicionados, o input é apenas para o valor restante
        if self.pagamentos:
            # Pega o valor digitado no input (se não for o troco)
            valor_digitado = self._unformat_currency(self.input_recebido.text())
            total_pago = self.valor_recebido + valor_digitado
        else:
            # Se for o primeiro (e único) pagamento, pega o valor do input
            total_pago = self._unformat_currency(self.input_recebido.text())
            
        self.troco = max(0.0, total_pago - self.total_venda)
        
        self._update_troco_display()
        
    def _update_troco_display(self):
        """Atualiza a label de troco e o estado do botão Confirmar."""
        troco_str = self._format_currency(self.troco)
        self.label_troco.setText(f"R$ {troco_str}")
        
        # Habilita o botão Confirmar se o valor pago for suficiente (troco >= 0)
        if self.valor_recebido + self._unformat_currency(self.input_recebido.text()) >= self.total_venda:
            self.btn_confirmar.setEnabled(True)
        else:
            self.btn_confirmar.setEnabled(False)
            
    def _confirmar_pagamento(self):
        """
        Finaliza o fluxo, armazena o último pagamento se necessário e aceita o diálogo.
        """
        
        # Se houver valor digitado e não foi adicionado (pagamento único)
        valor_input = self._unformat_currency(self.input_recebido.text())
        
        if not self.pagamentos and valor_input > 0:
            # Pagamento simples: Apenas um método e já calculado o troco
            self.pagamentos.append({'metodo': self.combo_metodo.currentText(), 'valor': self.total_venda - self.troco})
            self.valor_recebido = self.total_venda + self.troco # Valor total que o cliente deu (troco é a diferença)
        
        # Se for um pagamento misto, o valor do input restante precisa ser adicionado como o troco

        self.accept()
        
    def get_venda_data(self):
        """Retorna os dados necessários para o VendasController."""
        return {
            'valor_recebido': self.total_venda + self.troco, # Total que o cliente deu
            'troco': self.troco,
            # Se a lista de pagamentos foi usada, o valor é distribuído.
            # Se não, o valor é o total da venda.
            'pagamentos': self.pagamentos if self.pagamentos else [{'metodo': self.combo_metodo.currentText(), 'valor': self.total_venda}]
        }