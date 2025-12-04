# ui/main_window.py

import sqlite3
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QTableView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem

# Importa a lógica (core)
from core.database import connect_db, create_and_populate_tables 
from core.cart_logic import CartManager
# Importa as novas janelas
from ui.product_registration import ProductRegistrationWindow
from ui.product_list import ProductListWindow 

class PDVWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDV - Modularizado e Profissional")
        self.setGeometry(100, 100, 1000, 700)
        
        self.cart_manager = CartManager()
        
        self.db_connection = connect_db(self)
        if self.db_connection:
            create_and_populate_tables(self.db_connection)

        self._setup_ui()
        self._setup_cart_model()

    # --- Métodos de Lógica ---

    def _update_total_display(self, total: float):
        """Atualiza o display de total formatando corretamente."""
        formatted_total = f"R$ {total:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        self.total_display.setText(formatted_total)

    def _update_cart_table(self):
        """Atualiza a QTableView com os dados do CartManager."""
        self.cart_model.setRowCount(0) 
        
        for item in self.cart_manager.cart_items:
            row = []
            total_item = item['preco'] * item['quantidade']
            
            # 1. Código
            item_codigo = QStandardItem(item['codigo'])
            item_codigo.setTextAlignment(Qt.AlignCenter)
            row.append(item_codigo)
            
            # 2. Nome
            row.append(QStandardItem(item['nome']))
            
            # 3. Preço Unitário (Formatado)
            item_preco = QStandardItem(f"{item['preco']:,.2f}")
            item_preco.setTextAlignment(Qt.AlignRight)
            row.append(item_preco)
            
            # 4. Quantidade
            item_quant = QStandardItem(str(item['quantidade']))
            item_quant.setTextAlignment(Qt.AlignCenter)
            row.append(item_quant)

            # 5. Total por Item (Formatado)
            item_total = QStandardItem(f"{total_item:,.2f}")
            item_total.setTextAlignment(Qt.AlignRight)
            row.append(item_total)
            
            self.cart_model.appendRow(row)
        
        self.cart_table.scrollToBottom() # Mantém o scroll no item adicionado

    def _handle_add_item(self):
        """Busca o produto no BD e delega a adição ao CartManager."""
        code = self.search_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Aviso", "Por favor, digite um código de produto.")
            return

        if self.db_connection:
            cursor = self.db_connection.cursor()
            # Busca pelo CÓDIGO (agora pode ser o código alfanumérico)
            cursor.execute("SELECT codigo, nome, preco, tipo FROM Produtos WHERE codigo = ?", (code,))
            result = cursor.fetchone()
            
            if result:
                # Chama a lógica do carrinho (passa a tupla completa)
                self.cart_manager.add_item(result)
                
                # Atualiza a interface
                total = self.cart_manager.calculate_total()
                self._update_total_display(total)
                self._update_cart_table() 
                
            else:
                QMessageBox.critical(self, "Erro", f"Produto com código '{code}' não encontrado.")

        self.search_input.clear()
        self.search_input.setFocus()

    def _handle_remove_item(self):
        """Lê o código de busca e delega a remoção ao CartManager."""
        code = self.search_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Aviso", "Por favor, digite o código do produto para remover.")
            return

        self.cart_manager.remove_item(code) 
        
        total = self.cart_manager.calculate_total()
        self._update_total_display(total)
        self._update_cart_table() 

        self.search_input.clear()
        self.search_input.setFocus()
        
    def _handle_finalize_sale(self):
        """Finaliza a venda, valida valores e limpa o carrinho."""
        
        total = self.cart_manager.calculate_total()
        
        try:
            received_text = self.received_input.text().replace(',', '.').strip()
            received = float(received_text)
        except ValueError:
            QMessageBox.critical(self, "Erro de Valor", "Valores de Recebido são inválidos.")
            return

        if total <= 0:
            QMessageBox.warning(self, "Aviso", "Carrinho está vazio. Venda não finalizada.")
            return

        troco = received - total

        if troco < 0:
            QMessageBox.critical(self, "Valor Insuficiente", f"Faltam R$ {abs(troco):.2f}. Valor recebido é menor que o total.")
            return

        formatted_troco = f"R$ {troco:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        QMessageBox.information(self, "Venda Concluída", f"Troco: {formatted_troco}")
        
        # NOTE: AQUI DEVERIA IR A FUNÇÃO DE PERSISTÊNCIA DA VENDA NA TABELA 'VENDAS'
        
        # Limpa o carrinho e a interface
        self.cart_manager.clear_cart()
        self._update_cart_table()
        self._update_total_display(0.0)
        self.received_input.setText("0.00")
        self.search_input.setFocus()

    # --- Métodos para Abrir Novas Janelas ---

    def _handle_open_registration(self):
        """Abre a janela de cadastro de produtos."""
        self.registration_window = ProductRegistrationWindow(self.db_connection)
        self.registration_window.exec()

    def _handle_open_product_list(self):
        """Abre a janela de consulta e listagem de produtos."""
        self.list_window = ProductListWindow(self.db_connection)
        self.list_window.exec()
        
    # --- Configurações da UI e Atalhos ---

    def keyPressEvent(self, event):
        """Captura eventos de teclado para implementar atalhos (shortcuts) essenciais ao PDV."""
        
        if event.key() == Qt.Key_F4:
            self._handle_remove_item()
        
        elif event.key() == Qt.Key_F12:
            total = self.cart_manager.calculate_total()
            
            if self.received_input.hasFocus() and total > 0:
                self._handle_finalize_sale()
            elif total > 0:
                self.received_input.setFocus()
            
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            
            if self.search_input.hasFocus():
                self._handle_add_item()
            
            elif self.received_input.hasFocus() and self.cart_manager.calculate_total() > 0:
                self._handle_finalize_sale()

        super().keyPressEvent(event)

    def _setup_cart_model(self):
        """Configura o Modelo de dados para a QTableView."""
        self.cart_model = QStandardItemModel(0, 5) 
        self.cart_model.setHorizontalHeaderLabels(["CÓDIGO", "NOME", "PREÇO UN.", "QUANT.", "TOTAL ITEM"])
        self.cart_table.setModel(self.cart_model)
        self.cart_table.setColumnWidth(1, 300)
        self.cart_table.setColumnWidth(2, 100)
        self.cart_table.setColumnWidth(3, 80)
        self.cart_table.setColumnWidth(4, 100)

    def _setup_ui(self):
        """Configura os layouts e widgets da janela."""
        
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # --- Painel Esquerdo: Carrinho e Lista de Produtos (80% da tela) ---
        cart_panel = QWidget()
        cart_layout = QVBoxLayout(cart_panel)
        
        # 1. Campo de Busca/Código
        search_layout = QHBoxLayout()
        search_label = QLabel("Código/Busca:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o código (Ex: A001) e pressione Enter")
        self.search_input.setFont(QFont("Arial", 14))
        
        add_button = QPushButton("Adicionar (Enter)")
        add_button.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        add_button.clicked.connect(self._handle_add_item)

        remove_button = QPushButton("Remover (F4)")
        remove_button.setStyleSheet("background-color: #FF9800; color: white; padding: 10px;") 
        remove_button.clicked.connect(self._handle_remove_item)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(add_button)
        search_layout.addWidget(remove_button)
        
        cart_layout.addLayout(search_layout)
        
        # 2. Tabela do Carrinho (QTableView)
        self.cart_table = QTableView()
        cart_layout.addWidget(QLabel("ITENS DO CARRINHO"))
        cart_layout.addWidget(self.cart_table) 
        
        main_layout.addWidget(cart_panel, 8) 

        # --- Painel Direito: Total e Finalização (20% da tela) ---
        checkout_panel = QWidget()
        checkout_layout = QVBoxLayout(checkout_panel)
        
        # 1. Área do TOTAL (Display)
        self.total_display = QLabel("R$ 0,00")
        self.total_display.setFont(QFont("Arial", 32, QFont.Bold))
        self.total_display.setAlignment(Qt.AlignCenter)
        self.total_display.setStyleSheet("background-color: #D32F2F; color: white; padding: 20px; border-radius: 5px;")
        
        checkout_layout.addWidget(QLabel("TOTAL DA VENDA:", alignment=Qt.AlignCenter))
        checkout_layout.addWidget(self.total_display)
        checkout_layout.addSpacing(40) 

        # 2. Campo de Valor Recebido
        checkout_layout.addWidget(QLabel("VALOR RECEBIDO:", alignment=Qt.AlignCenter))
        self.received_input = QLineEdit("0.00")
        self.received_input.setFont(QFont("Arial", 16))
        self.received_input.setAlignment(Qt.AlignCenter)
        checkout_layout.addWidget(self.received_input)
        
        # 3. Botões Administrativos
        
        list_button = QPushButton("📋 Consultar Produtos")
        list_button.setFont(QFont("Arial", 12))
        list_button.setStyleSheet("background-color: #008CBA; color: white; padding: 10px; border-radius: 5px;")
        list_button.clicked.connect(self._handle_open_product_list)
        checkout_layout.addWidget(list_button) 
        
        register_button = QPushButton("✏️ Cadastrar Produto")
        register_button.setFont(QFont("Arial", 12))
        register_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 5px;")
        register_button.clicked.connect(self._handle_open_registration)
        checkout_layout.addWidget(register_button)
        
        # 4. Botão Finalizar
        finalize_button = QPushButton("FINALIZAR VENDA (F12)")
        finalize_button.setFont(QFont("Arial", 18, QFont.Bold))
        finalize_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px;")
        finalize_button.clicked.connect(self._handle_finalize_sale)

        checkout_layout.addWidget(finalize_button)
        checkout_layout.addStretch(1) 
        
        main_layout.addWidget(checkout_panel, 2) 

        self.setCentralWidget(central_widget)
        self.search_input.setFocus()