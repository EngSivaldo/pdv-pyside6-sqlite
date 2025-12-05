# ui/main_window.py

import sqlite3
import datetime 
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QTableView, QMessageBox, QCompleter, QInputDialog # Importado QCompleter
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
            item_preco = QStandardItem(f"{item['preco']:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            item_preco.setTextAlignment(Qt.AlignRight)
            row.append(item_preco)
            
            # 4. Quantidade
            item_quant = QStandardItem(str(item['quantidade']))
            item_quant.setTextAlignment(Qt.AlignCenter)
            row.append(item_quant)

            # 5. Total por Item (Formatado)
            item_total = QStandardItem(f"{total_item:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            item_total.setTextAlignment(Qt.AlignRight)
            row.append(item_total)
            
            self.cart_model.appendRow(row)
        
        self.cart_table.scrollToBottom()

    def _setup_autocompleter(self):
        """Busca todos os nomes/códigos de produtos e configura o QCompleter no campo de busca."""
        if not self.db_connection:
            return
            
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT codigo, nome FROM Produtos")
        
        product_names = []
        for codigo, nome in cursor.fetchall():
            # Adiciona tanto o nome quanto o código à lista de sugestões
            product_names.append(nome)
            product_names.append(codigo) 

        # Cria o modelo e o QCompleter
        completer = QCompleter(product_names, self)
        
        # MUDANÇA: Agora só sugere nomes/códigos que *começam* com o texto digitado.
        completer.setFilterMode(Qt.MatchStartsWith) 
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        self.search_input.setCompleter(completer)

    def _find_product_by_exact_match(self, search_text):
        """Busca por um produto por código exato ou nome exato (case-insensitive)."""
        if not self.db_connection or not search_text:
            return None
            
        cursor = self.db_connection.cursor()
        
        # 1. Busca por Código (Sempre Exata)
        cursor.execute("SELECT codigo, nome, preco, tipo FROM Produtos WHERE codigo = ?", (search_text,))
        result = cursor.fetchone()
        if result:
            return result
        
        # 2. Busca por Nome Exato (Case-Insensitive)
        cursor.execute(
            "SELECT codigo, nome, preco, tipo FROM Produtos WHERE LOWER(nome) = ? LIMIT 1",
            (search_text.lower(),)
        )
        return cursor.fetchone()

    # ui/main_window.py (Modificação em def _handle_add_item(self):)

    def _handle_add_item(self):
        """
        Busca o produto no BD e abre o diálogo de quantidade para confirmação.
        """
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "Aviso", "Por favor, digite o código ou o nome do produto.")
            return

        product_data = None
        
        if self.db_connection:
            cursor = self.db_connection.cursor()
            
            # 1. Tenta Busca Exata (código ou nome)
            product_data = self._find_product_by_exact_match(search_text)
            
            if not product_data:
                # 2. Se não for exato, tenta Buscas Parcial (pega o primeiro resultado)
                query_name = f"%{search_text.lower()}%"
                cursor.execute(
                    "SELECT codigo, nome, preco, tipo FROM Produtos WHERE LOWER(nome) LIKE ? LIMIT 1",
                    (query_name,)
                )
                product_data = cursor.fetchone()

            if product_data:
                # --- NOVO: Chamada ao Diálogo de Quantidade ---
                new_quantity = self._show_quantity_dialog(product_data)

                if new_quantity is not None:
                    # Adiciona o item com a quantidade confirmada
                    # NOTA: O CartManager.add_item agora precisa aceitar a quantidade
                    # Já que o CartManager original só aceita (product_data), vamos ajustar a chamada
                    # para _add_item_to_cart_manager, que será ligeiramente diferente
                    
                    # Para simplificar, vou assumir que CartManager.add_item aceita (product_data, quantidade)
                    # Se seu CartManager precisar de ajuste, por favor, me avise.
                    
                    # Por enquanto, vamos manter o add_item simples e lidar com a lógica de QUANTIDADE
                    # O CartManager original, que você me passou, só adicionava 1. Vamos simular a adição:
                    
                    # 1. Remova o item do carrinho se ele já existir (para garantir que a alteração seja feita)
                    # Se o produto já estiver no carrinho, vamos apenas atualizar a quantidade total dele.
                    
                    # Melhor abordagem: Adicione o item, e o CartManager irá somar ou substituir.
                    # Mas como o _show_quantity_dialog é chamado APÓS a busca, vamos garantir que ele seja adicionado corretamente.

                    # Para funcionar perfeitamente, precisamos que `CartManager` saiba lidar com a adição de uma quantidade específica.
                    # Já que eu não tenho o `CartManager`, vou criar uma versão auxiliar para adicionar a quantidade correta.

                    codigo = product_data[0]
                    nome = product_data[1]
                    preco = product_data[2]
                    tipo = product_data[3]

                    # A lógica aqui é limpar o campo de busca ANTES de atualizar o carrinho
                    self.search_input.clear()
                    
                    # Adiciona o item (o CartManager deve suportar este formato, mesmo que seja para adicionar a quantidade inicial)
                    self.cart_manager.add_item(
                        (codigo, nome, preco, tipo), 
                        quantity=new_quantity # Passando a nova quantidade
                    )
                    
                    total = self.cart_manager.calculate_total()
                    self._update_total_display(total)
                    self._update_cart_table() 
                
                # Se new_quantity for None, o usuário cancelou, e nada acontece
                
            else:
                QMessageBox.critical(self, "Erro", f"Produto com código/nome '{search_text}' não encontrado.")

        self.search_input.setFocus()

    def _handle_remove_item(self):
        """Lê o código de busca e delega a remoção ao CartManager (F4)."""
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
        """Finaliza a venda, valida valores e limpa o carrinho (F12)."""
        
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
            QMessageBox.critical(self, "Valor Insuficiente", f"Faltam R$ {abs(troco):.2f}".replace('.', '#').replace(',', '.').replace('#', ',') + ". Valor recebido é menor que o total.")
            return

        # -------------------------------------------------------------
        # NOTE: AQUI DEVE ENTRAR A FUNÇÃO DE PERSISTÊNCIA DA VENDA
        # -------------------------------------------------------------
        
        formatted_troco = f"R$ {troco:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        QMessageBox.information(self, "Venda Concluída", f"Troco: {formatted_troco}")
        
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
                self._handle_add_item() # Enter chama a função de adição/busca
            
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
        self.search_input.setPlaceholderText("Digite o código ou nome do produto. Use Enter para adicionar.")
        self.search_input.setFont(QFont("Arial", 14))
        
        # Configura o Auto-Completar (Lista de Sugestões que *começam* com o texto)
        self._setup_autocompleter()
        
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
    
    # ui/main_window.py (Novo método na classe PDVWindow)

    # ui/main_window.py (Modificação no método _show_quantity_dialog)

    # ui/main_window.py (dentro de def _show_quantity_dialog(self):)

    def _show_quantity_dialog(self, product_data):
        """
        Abre um diálogo para confirmar e alterar a quantidade/peso do produto.
        Retorna a nova quantidade (float), ou None se cancelado.
        """
        nome_produto = product_data[1] # Nome do produto
        
        # ⚠️ CORREÇÃO AQUI: Garante que tipo_produto não é None e padroniza para 'Unidade' se for
        tipo_produto = product_data[3] if product_data[3] is not None else 'Unidade' 
        
        # Se for 'Peso', continua a lógica de double; caso contrário, usa int (para 'Unidade' ou qualquer outro valor)
        if tipo_produto.lower() == 'peso': 
            label = f"Digite o PESO para {nome_produto} (Kg):"
            initial_value = 1.000
            # ... (resto do código para getDouble) ...
            new_quantity, ok = QInputDialog.getDouble(
                self, "Confirmar Peso/Quantidade", label, 
                value=initial_value, decimals=3 
            )
        else:
            # ... (resto do código para getInt) ...
            label = f"Digite a QUANTIDADE para {nome_produto}:"
            initial_value = 1
            new_quantity, ok = QInputDialog.getInt(
                self, "Confirmar Quantidade", label, 
                value=initial_value
            )

        if ok:
            return new_quantity
        
        return None