# ui/main_window.py - VERSÃO LIMPA (SEM DEBUG)

import sqlite3
import datetime 
import os 
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QTableView, QMessageBox, QCompleter, QInputDialog, QDialog 
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem

# IMPORTS PARA NORMALIZAÇÃO/BUSCA SEM ACENTOS
from unidecode import unidecode
import re

# Importa a lógica (core)
from core.database import connect_db, create_and_populate_tables 
from core.cart_logic import CartManager
# Importa as novas janelas
from ui.product_registration import ProductRegistrationWindow
from ui.product_list import ProductListWindow 
from ui.checkout_dialog import CheckoutDialog
from .cadastro_funcionario_dialog import CadastroFuncionarioDialog 
from .gerenciar_funcionarios_dialog import GerenciarFuncionariosDialog
from ui.gerenciar_produtos_dialog import GerenciarProdutosDialog

# ----------------------------------------------------
# --- FUNÇÕES DE NORMALIZAÇÃO PARA BUSCA (PDV) ---
# ----------------------------------------------------

def normalize_text(text):
    """
    Converte o texto para minúsculas e remove acentos/cedilhas 
    usando unidecode para uma busca robusta.
    """
    if text is None:
        return ""
    text_str = str(text).strip()
    normalized = unidecode(text_str)
    return normalized.lower()

def clean_for_comparison(text):
    """Remove caracteres especiais, espaços e pontuações do texto normalizado."""
    normalized = normalize_text(text)
    # Remove qualquer coisa que não seja letra ou número (a-z, 0-9)
    cleaned = re.sub(r'[^a-z0-9]', '', normalized) 
    return cleaned


# ----------------------------------------------------
# --- CLASSE PRINCIPAL PDVWindow ---
# ----------------------------------------------------

class PDVWindow(QMainWindow):
    def __init__(self, db_connection, logged_user, parent=None): # ⭐️ CORREÇÃO 1: Aceita argumentos
        super().__init__(parent)
        
        # ⭐️ CORREÇÃO 2: Armazena a conexão e o usuário logado 
        self.db_connection = db_connection 
        self.logged_user = logged_user 
        
        # ⭐️ CORREÇÃO 3: Define o título com o nome e cargo do usuário logado
        self.setWindowTitle(f"PDV - Usuário: {self.logged_user['nome']} ({self.logged_user['cargo'].upper()})")
        
        self.setGeometry(100, 100, 1000, 700)
        
        self.cart_manager = CartManager()
        
        # Estado do tema (dark é o padrão styles.qss)
        self.current_theme = 'dark' 
        
        # ❌ A lógica de connect_db() e create_and_populate_tables() foi removida daqui, 
        # pois agora é tratada de forma centralizada no main.py, antes do login.
        
        # --- APLICAÇÃO DO STYLESHEET ---
        self._apply_stylesheet('styles.qss') # Carrega o tema dark padrão
        # -----------------------------------------------

        self._setup_ui()
        self._setup_cart_model()

    # Em ui/main_window.py, dentro do método _show_employee_registration:

    def _show_employee_registration(self):
        # Usamos argumentos nomeados para garantir que 'self' seja o 'parent'
        # e que 'employee_id' seja explicitamente None, forçando o MODO CADASTRO.
        dialog = CadastroFuncionarioDialog(
            db_connection=self.db_connection, 
            employee_id=None, 
            parent=self
        )
        dialog.exec()
    
    def _show_product_management(self):
        """Abre o diálogo de gerenciamento de produtos."""
        # Instancia o diálogo, passando a conexão ativa com o banco de dados
        dialog = GerenciarProdutosDialog(
            db_connection=self.db_connection, 
            parent=self
        )
        dialog.exec()

    # ----------------------------------------------------
    # --- MÉTODOS DE CONTROLE DE TEMA E ESTILO ---
    # ----------------------------------------------------

    def _apply_stylesheet(self, filename):
        """Carrega e aplica o stylesheet dado pelo nome do arquivo (localizado na raiz do projeto)."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Volta um nível para a pasta raiz do projeto
        style_path = os.path.join(base_dir, '..', filename) 
        
        if os.path.exists(style_path):
            try:
                with open(style_path, 'r') as f:
                    self.setStyleSheet(f.read())
                # print(f"LOG: Stylesheet '{filename}' carregado com sucesso.")
                return True
            except Exception as e:
                # print(f"ERRO ao carregar o stylesheet '{filename}': {e}")
                return False
        else:
            # print(f"ALERTA: Stylesheet '{filename}' não encontrado em: {style_path}")
            return False

    def _toggle_theme(self):
        """Alterna entre o tema Dark (styles.qss) e o tema Light (styles_light.qss)."""
        
        if self.current_theme == 'dark':
            # Tenta carregar o tema CLARO
            if self._apply_stylesheet('styles_light.qss'):
                self.current_theme = 'light'
                # Próxima opção deve ser ESCURO
                self.theme_button.setText("Tema: 🌙 ESCURO") 
                self.theme_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 5px;")
        
        else: # current_theme == 'light'
            # Tenta carregar o tema ESCURO
            if self._apply_stylesheet('styles.qss'): # styles.qss é o seu tema ESCURO original
                self.current_theme = 'dark'
                # Próxima opção deve ser CLARO
                self.theme_button.setText("Tema: ☀️ CLARO") 
                self.theme_button.setStyleSheet("background-color: #9E9E9E; color: white; padding: 10px; border-radius: 5px;")


    # ----------------------------------------------------
    # --- MÉTODOS DE LÓGICA E INTERFACE ---
    # ----------------------------------------------------
    
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
            
            # 4. Quantidade (Formatada para peso ou unidade)
            tipo = item.get('tipo', 'Unidade').lower()
            if tipo == 'peso':
                # Mostra 3 casas decimais para peso
                quant_str = f"{item['quantidade']:,.3f}".replace('.', '#').replace(',', '.').replace('#', ',')
            else:
                # Mostra 0 ou 2 casas decimais para unidade/outros
                quant_str = f"{item['quantidade']:.0f}" if item['quantidade'].is_integer() else f"{item['quantidade']:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
                
            item_quant = QStandardItem(quant_str)
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
        
        product_suggestions = []
        for codigo, nome in cursor.fetchall():
            product_suggestions.append(nome)
            product_suggestions.append(codigo) 
            
        completer = QCompleter(product_suggestions, self)
        
        # ⭐️ CORREÇÃO CHAVE: Usar MatchContains permite que a busca encontre o termo digitado em qualquer lugar da string.
        completer.setFilterMode(Qt.MatchStartsWith)
        
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        # Conecta o completer ao campo de entrada
        self.search_input.setCompleter(completer)

    def _show_quantity_dialog(self, product_data):
        """
        Abre um diálogo para confirmar e alterar a quantidade/peso do produto.
        Retorna a nova quantidade (float), ou None se cancelado.
        
        Atenção: product_data[3] agora é 'tipo_medicao'.
        """
        
        # Cria uma instância do QInputDialog e remove temporariamente o stylesheet
        dialog = QInputDialog(self)
        dialog.setStyleSheet("") 
        
        # O product_data é a tupla de 5 elementos: (codigo, nome, preco, tipo_medicao, categoria)
        nome_produto = product_data[1]
        # Usamos o índice 3, que agora é tipo_medicao
        tipo_produto = product_data[3] if product_data[3] is not None else 'Unidade' 
        
        if tipo_produto.lower() == 'peso': 
            label = f"Digite o PESO para {nome_produto} (Kg):"
            initial_value = 1.000
            
            new_quantity, ok = dialog.getDouble(
                dialog, "Confirmar Peso/Quantidade", label, 
                value=initial_value, decimals=3 
            )
        else:
            label = f"Digite a QUANTIDADE para {nome_produto}:"
            initial_value = 1
            new_quantity, ok = dialog.getInt(
                dialog, "Confirmar Quantidade", label, 
                value=initial_value
            )

        if ok and new_quantity > 0:
            return float(new_quantity) # Garante que o retorno é float
        
        return None
    
    def _handle_add_item(self):
        """
        Lida com a adição de item ao carrinho, incluindo busca exata, busca por código 
        limpo/nome limpo e tratamento de ambiguidade (múltiplos matches).
        """
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "Aviso", "Por favor, digite o código ou o nome do produto.")
            return

        product_data = None
        
        # 1. NORMALIZAÇÃO DA BUSCA
        normalized_search = clean_for_comparison(search_text) 
        
        if self.db_connection:
            cursor = self.db_connection.cursor()
            
            # 2. Busca por Código Exato (Prioridade Máxima)
            # CORRIGIDO: Selecionando as 5 colunas da nova estrutura
            cursor.execute("SELECT codigo, nome, preco, tipo_medicao, categoria FROM Produtos WHERE codigo = ?", (search_text,))
            product_data = cursor.fetchone()

            # 3. Busca Parcial (se não encontrou por código exato)
            if not product_data:
                # CORRIGIDO: Selecionando as 5 colunas da nova estrutura
                cursor.execute("SELECT codigo, nome, preco, tipo_medicao, categoria FROM Produtos")
                all_products = cursor.fetchall()
                
                matching_products = []
                
                for row in all_products:
                    # CORRIGIDO: Desempacotando as 5 colunas
                    codigo, nome, preco, tipo_medicao, categoria = row
                    
                    # Normaliza o nome e o código do produto no BD para comparação
                    normalized_name_db = clean_for_comparison(nome)
                    normalized_codigo_db = clean_for_comparison(codigo)
                    
                    # Verifica se o texto normalizado de busca está CONTIDO no código OU no nome normalizado do BD
                    if normalized_search in normalized_codigo_db or normalized_search in normalized_name_db:
                        matching_products.append(row)

                # Analisa os matches parciais
                if len(matching_products) == 1:
                    # Achou um match único
                    product_data = matching_products[0]
                
                elif len(matching_products) > 1:
                    # Encontrou múltiplos matches (ambiguidade)
                    
                    # ⭐️ 1. Chama a nova função de seleção (vamos criá-la logo abaixo)
                    selected_product = self._show_selection_dialog(matching_products)
                    
                    if selected_product:
                        # Se o usuário escolheu, product_data recebe o item escolhido
                        product_data = selected_product 
                        # O fluxo continua para o Passo 4 (Lógica de Adição)
                        
                    else:
                        # Se o usuário cancelou o diálogo de seleção, limpamos e saímos.
                        self.search_input.clear() 
                        self.search_input.setFocus()
                        return # Sai da função sem adicionar nada
                    
            # 4. Lógica de Adição (executada APENAS se product_data for encontrado e não for ambíguo)
            if product_data:
                
                # Chama o diálogo de quantidade (usa product_data[3], que agora é tipo_medicao)
                new_quantity = self._show_quantity_dialog(product_data)

                if new_quantity is not None:
                    # Passa a tupla de 5 elementos para o CartManager. 
                    # Assumimos que o CartManager usa o 4º elemento (índice 3: tipo_medicao) como 'tipo'.
                    self.cart_manager.add_item(
                        product_data, 
                        quantity=new_quantity 
                    )
                    
                    self.search_input.clear()
                    total = self.cart_manager.calculate_total()
                    self._update_total_display(total)
                    self._update_cart_table() 
            
            else:
                # Se não encontrou nem por código exato, nem por nome único
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

    def _record_sale(self, total: float, received: float, change: float):
        """Registra a transação de venda e seus itens no banco de dados."""
        if not self.db_connection: return False

        try:
            cursor = self.db_connection.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Registrar a Venda Principal
            cursor.execute(
                "INSERT INTO Vendas (data_hora, total_venda, valor_recebido, troco) VALUES (?, ?, ?, ?)",
                (timestamp, total, received, change)
            )
            venda_id = cursor.lastrowid 

            # 2. Registrar os Itens da Venda
            items_to_insert = []
            for item in self.cart_manager.cart_items:
                items_to_insert.append((
                    venda_id,
                    item['codigo'],
                    item['nome'],
                    item['quantidade'],
                    item['preco'] 
                ))

            cursor.executemany(
                "INSERT INTO ItensVenda (venda_id, produto_codigo, nome_produto, quantidade, preco_unitario) VALUES (?, ?, ?, ?, ?)",
                items_to_insert
            )
            
            self.db_connection.commit()
            return True

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Falha ao registrar a venda: {e}")
            self.db_connection.rollback()
            return False
    
    def _handle_finalize_sale(self):
        """Abre o diálogo de Checkout para confirmação de pagamento e registra a venda."""
        
        total = self.cart_manager.calculate_total()
        
        if total <= 0:
            QMessageBox.warning(self, "Aviso", "Carrinho está vazio. Venda não finalizada.")
            return
            
        checkout_dialog = CheckoutDialog(total_venda=total, parent=self)
        
        if checkout_dialog.exec() == QDialog.Accepted:
            # Venda foi aceita na tela de Checkout
            received = checkout_dialog.valor_recebido
            troco = checkout_dialog.troco
            
            if not self._record_sale(total, received, troco): 
                return

            formatted_troco = f"R$ {troco:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
            QMessageBox.information(self, "Venda Concluída", f"Troco: {formatted_troco}")
            
            # Limpa o carrinho e a interface
            self.cart_manager.clear_cart()
            self._update_cart_table()
            self._update_total_display(0.0)
            self.received_input.setText("0.00")
            self.search_input.setFocus()
    
    # --- EDIÇÃO DE QUANTIDADE POR CLIQUE DUPLO ---
    
    def _handle_edit_quantity(self, index):
        """Lida com o clique duplo na tabela para editar a quantidade do item."""
        
        QUANTITY_COLUMN_INDEX = 3
        CODE_COLUMN_INDEX = 0

        if index.column() != QUANTITY_COLUMN_INDEX:
            return

        row = index.row()
        # Pega o código do produto para buscar o item no CartManager
        codigo = self.cart_model.data(self.cart_model.index(row, CODE_COLUMN_INDEX))
        
        current_item = next((item for item in self.cart_manager.cart_items if item['codigo'] == codigo), None)
        
        if not current_item:
            QMessageBox.warning(self, "Erro", "Item não encontrado no carrinho.")
            return

        current_quantity = current_item['quantidade']
        # Usa a chave 'tipo', que é como o CartManager armazena a informação (originalmente index 3)
        tipo = current_item.get('tipo', 'Unidade').lower() 
        
        # Cria um diálogo temporário sem estilo para evitar warnings
        dialog = QInputDialog(self)
        dialog.setStyleSheet("") 

        if tipo == 'peso':
            label = f"Novo PESO para {current_item['nome']} (Kg):"
            initial_value = float(current_quantity)
            
            new_quantity, ok = dialog.getDouble(
                self, "Editar Peso/Quantidade", label, 
                value=initial_value, decimals=3 
            )
        else:
            label = f"Nova QUANTIDADE para {current_item['nome']}:"
            # Tenta usar int para unidade
            initial_value = int(current_quantity) if current_quantity.is_integer() else round(current_quantity)

            new_quantity, ok = dialog.getInt(
                self, "Editar Quantidade", label, 
                value=initial_value
            )

        if ok and new_quantity is not None:
            if new_quantity <= 0:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Remover Item")
                msg_box.setText("Quantidade zero ou negativa. Deseja remover o item do carrinho?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                
                if msg_box.exec() == QMessageBox.Yes:
                    # update_quantity com 0 remove
                    self.cart_manager.update_quantity(codigo, 0) 
                else:
                    return 
            else:
                self.cart_manager.update_quantity(codigo, float(new_quantity))

            total = self.cart_manager.calculate_total()
            self._update_total_display(total)
            self._update_cart_table()

    # ----------------------------------------------------
    # --- MÉTODOS DE SETUP E EVENTOS ---
    # ----------------------------------------------------

    def keyPressEvent(self, event):
        """Captura eventos de teclado para implementar atalhos (shortcuts)."""
        
        if event.key() == Qt.Key_F4:
            self._handle_remove_item()
        
        elif event.key() == Qt.Key_F12:
            if self.cart_manager.calculate_total() > 0:
                self._handle_finalize_sale()
        
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.search_input.hasFocus():
                self._handle_add_item()
            
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
        self.cart_table.setSelectionBehavior(QTableView.SelectRows)
        self.cart_table.setEditTriggers(QTableView.NoEditTriggers)

        # Conecta o sinal de clique duplo para edição de quantidade
        self.cart_table.doubleClicked.connect(self._handle_edit_quantity)

    def _handle_open_registration(self):
        """Abre a janela de cadastro de produtos."""
        self.registration_window = ProductRegistrationWindow(self.db_connection)
        self.registration_window.exec()

    def _handle_open_product_list(self):
        """Abre a janela de consulta e listagem de produtos."""
        self.list_window = ProductListWindow(self.db_connection)
        self.list_window.exec()

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
        self.total_display.setObjectName("totalDisplay") # Importante para o Stylesheet
        self.total_display.setFont(QFont("Arial", 32, QFont.Bold))
        self.total_display.setAlignment(Qt.AlignCenter)
        
        checkout_layout.addWidget(QLabel("TOTAL DA VENDA:", alignment=Qt.AlignCenter))
        checkout_layout.addWidget(self.total_display)
        checkout_layout.addSpacing(40) 

        # 2. Campo de Valor Recebido (Apenas visual, o cálculo real está no CheckoutDialog)
        checkout_layout.addWidget(QLabel("VALOR RECEBIDO:", alignment=Qt.AlignCenter))
        self.received_input = QLineEdit("0.00")
        self.received_input.setFont(QFont("Arial", 16))
        self.received_input.setAlignment(Qt.AlignCenter)
        checkout_layout.addWidget(self.received_input)
        
        # 3. Botões Administrativos
        
        # Botão de Troca de Tema
        self.theme_button = QPushButton("Tema: ☀️ CLARO") 
        self.theme_button.setFont(QFont("Arial", 12))
        self.theme_button.setStyleSheet("background-color: #9E9E9E; color: white; padding: 10px; border-radius: 5px;")
        self.theme_button.clicked.connect(self._toggle_theme)
        checkout_layout.addWidget(self.theme_button) 
        
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
        
        # 1. Crie o botão para gerenciar produtos
        self.manage_products_button = QPushButton("📦 Gerenciar Produtos")
        
        # 2. Conecte o sinal 'clicked' ao método que abre o diálogo
        self.manage_products_button.clicked.connect(self._show_product_management)
        # ⬅️ INSERIR AQUI
        checkout_layout.addWidget(self.manage_products_button)
        # ➡️ FIM DA INSERÇÃO
        self.register_employee_button = QPushButton("👨‍💼 Cadastrar Funcionário")
    
        
        # ⭐️ NOVO BOTÃO: Cadastrar Funcionário ⭐️
        self.register_employee_button = QPushButton("👨‍💼 Cadastrar Funcionário")
        self.register_employee_button.setFont(QFont("Arial", 12))
        # Estilo Admin (vermelho/destacado, pois é uma função crítica)
        self.register_employee_button.setStyleSheet("background-color: #FF5722; color: white; padding: 10px; border-radius: 5px;") 
        self.register_employee_button.clicked.connect(self._show_employee_registration)
        checkout_layout.addWidget(self.register_employee_button)
        
        
        # Botão: Gerenciar Funcionários (Listar, Editar, Excluir)
        self.manage_employee_button = QPushButton("👥 Gerenciar Funcionários")
        self.manage_employee_button.setFont(QFont("Arial", 12))
        self.manage_employee_button.setStyleSheet("background-color: #03A9F4; color: white; padding: 10px; border-radius: 5px;") 
        self.manage_employee_button.clicked.connect(self._show_employee_management)
        checkout_layout.addWidget(self.manage_employee_button)
        
        is_admin = self.logged_user['cargo'] == 'admin'
        
        if not is_admin:
            # Oculta e desabilita o botão de Cadastro
            self.register_employee_button.setVisible(False)
            self.register_employee_button.setEnabled(False)
            
            # Oculta e desabilita o botão de Gerenciamento
            self.manage_employee_button.setVisible(False) 
            self.manage_employee_button.setEnabled(False)
        
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
    
    # Em ui/main_window.py, dentro da classe PDVWindow:

    # ... (depois de _show_employee_registration) ...
    
    def _show_employee_management(self):
        """
        Abre o diálogo de gerenciamento de funcionários.
        Passa a conexão com o banco de dados.
        """
        dialog = GerenciarFuncionariosDialog(self.db_connection, self)
        dialog.exec()
        
        