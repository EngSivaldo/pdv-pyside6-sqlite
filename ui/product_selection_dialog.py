from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt

class ProductSelectionDialog(QDialog):
    """
    Diálogo para resolver ambiguidade na busca, permitindo ao usuário 
    selecionar um produto de uma lista de matches parciais.
    """

    def __init__(self, matching_products: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleção de Produto (Múltiplos Resultados)")
        self.resize(600, 400)
        
        # Lista de tuplas do DB: (codigo, nome, preco, tipo_medicao, categoria)
        self.products = matching_products 
        self.selected_product = None
        
        self.setup_ui()
        self._populate_table()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(4) # Código, Nome, Preço, Categoria
        self.table.setHorizontalHeaderLabels(["Código", "Nome", "Preço (R$)", "Categoria"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Ajuste de cabeçalho
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Nome estica
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Ação ao dar duplo clique
        self.table.itemDoubleClicked.connect(self.accept_selection)
        main_layout.addWidget(self.table)
        
        # Botões
        button_layout = QHBoxLayout()
        select_button = QPushButton("✅ Selecionar (Enter)")
        select_button.clicked.connect(self.accept_selection)
        cancel_button = QPushButton("Cancelar (ESC)")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(select_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def _populate_table(self):
        """Preenche a tabela com os produtos que deram match."""
        self.table.setRowCount(len(self.products))
        
        for row_index, product in enumerate(self.products):
            codigo, nome, preco, tipo_medicao, categoria = product
            
            self.table.setItem(row_index, 0, QTableWidgetItem(codigo))
            self.table.setItem(row_index, 1, QTableWidgetItem(nome))
            
            # Formata o preço para exibição
            price_item = QTableWidgetItem(f"R$ {preco:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, 2, price_item)
            
            self.table.setItem(row_index, 3, QTableWidgetItem(categoria))

    def accept_selection(self):
        """Pega o produto selecionado na tabela e fecha o diálogo."""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Seleção Necessária", "Selecione um produto da lista.")
            return

        selected_row_index = selected_rows[0].row()
        self.selected_product = self.products[selected_row_index]
        self.accept()

    def get_selected_product(self):
        """Retorna a tupla de produto selecionada."""
        return self.selected_product

    def keyPressEvent(self, event):
        """Atalhos de teclado: Enter para confirmar e Escape para cancelar."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept_selection()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)