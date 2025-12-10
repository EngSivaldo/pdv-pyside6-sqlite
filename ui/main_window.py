# ui/main_window.py - VERSÃO LIMPA (SEM DEBUG)

import sqlite3
import datetime 
import os 
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QTableView, QMessageBox, QCompleter, QInputDialog, QDialog, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem,QKeySequence, QShortcut

# IMPORTS PARA NORMALIZAÇÃO/BUSCA SEM ACENTOS
from unidecode import unidecode
import re

# Importa a lógica (core)
from core.database import connect_db, create_and_populate_tables 
from core.cart_logic import CartManager
from core.database import finalizar_venda # <--- ADICIONE ESTA LINHA!
# Importa as novas janelas
from ui.product_registration import ProductRegistrationWindow
from ui.product_list import ProductListWindow 
from ui.checkout_dialog import CheckoutDialog
from .cadastro_funcionario_dialog import CadastroFuncionarioDialog 
from .gerenciar_funcionarios_dialog import GerenciarFuncionariosDialog
from ui.gerenciar_produtos_dialog import GerenciarProdutosDialog
from ui.relatorios_vendas_dialog import RelatoriosVendasDialog 
from core.database import finalizar_venda, update_stock_after_sale
from ui.weight_input_product_dialog import WeightInputProductDialog 
from ui.product_selection_dialog import ProductSelectionDialog
from ui.total_discount_dialog import TotalDiscountDialog
from data.vendas_controller import VendasController
from ui.post_sale_dialog import PostSaleDialog
from core.printer_manager import PrinterManager 

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
    """Remove acentos, pontuações e converte para minúsculas."""
    import re
    if text is None: return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text) # Remove pontuação
    text = re.sub(r'[áàãâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòõôö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    return text.strip()

# ----------------------------------------------------
# --- CLASSE PRINCIPAL PDVWindow ---
# ----------------------------------------------------

class PDVWindow(QMainWindow):
    # C:\Users\sival\Ponto de Venda\ui\main_window.py (Dentro da classe PDVWindow)

    def __init__(self, db_connection, logged_user, parent=None): # db_connection é a conexão aberta, mas VendasController precisa da FUNÇÃO de conexão
        super().__init__(parent)
        
        self.db_connection = db_connection 
        self.logged_user = logged_user 
        
        # 1.  CORREÇÃO: Inicialização dos atributos de desconto/taxa 
        # Estes são os valores que serão definidos pelo TotalDiscountDialog e lidos em _handle_finalize_sale
        self.total_discount_value = 0.0  
        self.service_fee_value = 0.0     
        
        # 2.  CORREÇÃO: Inicialização do VendasController 
        # Assumimos que o VendasController é inicializado sem a função connect_db, e que ele a chama internamente.
        # Se você implementou VendasController para ACEITAR A FUNÇÃO, use: self.vendas_controller = VendasController(connect_db)
        # Mas se ele se auto-inicializa, use:
        self.vendas_controller = VendasController()
        
        self.setWindowTitle(f"PDV - Usuário: {self.logged_user['nome']} ({self.logged_user['cargo'].upper()})")
        
        self.setGeometry(100, 100, 1000, 700)
        
        self.cart_manager = CartManager()
        
        # Estado do tema (dark é o padrão styles.qss)
        self.current_theme = 'dark' 
        
        # --- APLICAÇÃO DO STYLESHEET ---
        self._apply_stylesheet('styles.qss') # Carrega o tema dark padrão
        # -----------------------------------------------
        self.printer_manager = PrinterManager()

        self._setup_ui()
        self._setup_cart_model()

        # NOTA: O db_connection passado como argumento só é útil aqui se você
        # for usá-lo para outras queries que não sejam de venda. 
        # Para vendas, usamos self.vendas_controller.
    # C:\Users\sival\Ponto de Venda\ui\main_window.py (Dentro da classe PDVWindow)

    def _format_currency(self, value: float) -> str:
        """
        Formata um valor float para string de moeda brasileira (R$ X.XXX,XX).
        """
        if value is None:
            value = 0.0
            
        # Formatação que substitui o ponto decimal por vírgula e adiciona separador de milhar.
        # Ex: 1234.56 -> R$ 1.234,56
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    def _reset_cart(self):
        """Função auxiliar para limpar e resetar a interface após a venda."""
        self.cart_manager.clear_cart()
        self._update_cart_table() # Atualiza a tabela do carrinho
        self._update_total_display(0.0) # Zera o total
        self.search_input.setFocus()
        self.total_discount_value = 0.0 # Zera o desconto
        self.service_fee_value = 0.0    # Zera a taxa
        self._update_total_display(self._calculate_subtotal()) # Atualiza o total novamente

    # ui/main_window.py (Métodos _print_receipt e _print_invoice)

    # ui/main_window.py (Dentro de class PDVWindow:)

    def _print_receipt(self, sale_id: int):
        """Gera o recibo e simula a impressão (console/log)."""
        
        # ⭐️ CORREÇÃO: Usar o nome correto das variáveis inicializadas ⭐️
        venda_data = self.vendas_controller.last_venda_data 
        itens_carrinho = self.vendas_controller.last_itens_carrinho
        pagamentos = self.vendas_controller.last_pagamentos
        
        # CORREÇÃO ADICIONAL: Garante que o ID da venda esteja nos dados para o recibo
        venda_data['id'] = sale_id
        
        if not venda_data:
            QMessageBox.warning(self, "Erro de Impressão", "Dados da última venda não foram encontrados. Tente novamente.")
            return

        # 2. Geração do Conteúdo
        receipt_content = self.printer_manager.generate_receipt_content(
            venda_data, itens_carrinho, pagamentos
        )
        
        # 3. Impressão (Simulada no console)
        self.printer_manager.print_to_console(receipt_content)
        
        QMessageBox.information(
            self, 
            "Impressão", 
            f"Recibo da Venda #{sale_id} formatado e enviado (Verifique o console)."
        )


    def _print_invoice(self, sale_id: int):
        """Chama a rotina de emissão de NF-e/NFC-e (Simulação de API)."""
        
        # 1. Obter Dados (Idem ao recibo, precisa dos dados da venda por ID)
        venda_data = self.vendas_controller.last_venda_data 
        itens_carrinho = self.vendas_controller.last_itens_carrinho
        pagamentos = self.vendas_controller.last_pagamentos
        
        venda_data['id'] = sale_id
            
        # 2. Iniciar a Rotina Fiscal
        nf_log = self.printer_manager.initiate_invoice_emission(
            venda_data, itens_carrinho, pagamentos
        )
        
        # 3. Exibir Status
        QMessageBox.warning(
            self, 
            "Emissão NF", 
            f"Simulação de Emissão Fiscal para Venda #{sale_id} concluída.\nDetalhes no log:\n{nf_log}"
        )
        # Lógica real de integração fiscal vai aqui

    def _show_employee_registration(self):
        # Usamos argumentos nomeados para garantir que 'self' seja o 'parent'
        # e que 'employee_id' seja explicitamente None, forçando o MODO CADASTRO.
        dialog = CadastroFuncionarioDialog(
            db_connection=self.db_connection, 
            employee_id=None, 
            parent=self
        )
        dialog.exec()
    
    # Trecho em ui/main_window.py
    def _show_product_management(self):
        logged_user = self.logged_user # O dicionário do usuário logado
        
        # ⭐️ VERIFICAÇÃO DE ACESSO AQUI (Nível 1) ⭐️
        if logged_user.get('cargo') != 'admin':
            QMessageBox.warning(self, "Acesso Negado", "Apenas administradores podem gerenciar produtos.")
            return
            
        dialog = GerenciarProdutosDialog(
            db_connection=self.db_connection, 
            logged_user=logged_user, # Passa o objeto do usuário
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

    # Certifique-se de importar:
# from ui.product_selection_dialog import ProductSelectionDialog
# from ui.weight_input_product_dialog import WeightInputProductDialog
# import re
    from PySide6.QtWidgets import QDialog # Import necessário

    # Função auxiliar para normalização (fora da classe)
    def clean_for_comparison(text):
        """Remove acentos, pontuações e converte para minúsculas."""
        import re
        if text is None: return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text) # Remove pontuação
        text = re.sub(r'[áàãâä]', 'a', text)
        text = re.sub(r'[éèêë]', 'e', text)
        text = re.sub(r'[íìîï]', 'i', text)
        text = re.sub(r'[óòõôö]', 'o', text)
        text = re.sub(r'[úùûü]', 'u', text)
        text = re.sub(r'[ç]', 'c', text)
        return text.strip()

# Dentro da classe PDVWindow:

    def _show_selection_dialog(self, matching_products: list):
        """Chama o diálogo de seleção de produto para resolver a ambiguidade."""
        dialog = ProductSelectionDialog(matching_products, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_selected_product()
        else:
            return None

    def _show_quantity_dialog(self, product_data: tuple) -> float | None:
        """
        Decide qual diálogo de quantidade usar (Peso ou Unidade Padrão) 
        e retorna a quantidade final.
        """
        # A tupla product_data é: (codigo, nome, preco, tipo_medicao, categoria)
        
        # Se o tipo de medição for 'Peso', chama o diálogo de peso
        if product_data[3].lower() == 'peso':
            dialog = WeightInputProductDialog(
                product_name=product_data[1],  # nome
                product_price=product_data[2], # preco
                parent=self
            )
            
            if dialog.exec() == QDialog.Accepted:
                # Retorna a quantidade (peso)
                weight_qty, _ = dialog.get_weight_and_total()
                return weight_qty
            else:
                # Usuário cancelou a entrada de peso
                return None
        
        else:
            # Para "Unidade" ou qualquer outro, retorna 1 (Unidade Padrão)
            # O sistema pode ser expandido para chamar um diálogo de entrada 
            # de quantidade simples aqui, se necessário.
            return 1.0 # Adiciona 1 unidade por padrão
        
    def _handle_add_item(self):
        """
        Lida com a adição de item ao carrinho, incluindo busca exata, busca por código 
        limpo/nome limpo e tratamento de ambiguidade (múltiplos matches) e 
        lançamento de peso.
        """
        from PySide6.QtWidgets import QMessageBox, QDialog
        from ui.weight_input_product_dialog import WeightInputProductDialog
        
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
            # Tupla: (codigo, nome, preco, tipo_medicao, categoria)
            cursor.execute("SELECT codigo, nome, preco, tipo_medicao, categoria FROM Produtos WHERE codigo = ?", (search_text,))
            product_data = cursor.fetchone()

            # 3. Busca Parcial (se não encontrou por código exato)
            if not product_data:
                cursor.execute("SELECT codigo, nome, preco, tipo_medicao, categoria FROM Produtos")
                all_products = cursor.fetchall()
                
                matching_products = []
                
                for row in all_products:
                    codigo, nome, preco, tipo_medicao, categoria = row
                    
                    normalized_name_db = clean_for_comparison(nome)
                    normalized_codigo_db = clean_for_comparison(codigo)
                    
                    if normalized_search in normalized_codigo_db or normalized_search in normalized_name_db:
                        matching_products.append(row)

                # Analisa os matches parciais
                if len(matching_products) == 1:
                    # Achou um match único
                    product_data = matching_products[0]
                
                elif len(matching_products) > 1:
                    # Encontrou múltiplos matches (ambiguidade)
                    selected_product = self._show_selection_dialog(matching_products)
                    
                    if selected_product:
                        product_data = selected_product 
                    else:
                        # Usuário cancelou a seleção
                        self.search_input.clear() 
                        self.search_input.setFocus()
                        return # Sai da função

            # 4. Lógica de Adição (executada APENAS se product_data for encontrado)
            if product_data:
                
                # ⭐️ INÍCIO DA NOVA LÓGICA DE PESO/UNIDADE ⭐️
                codigo, nome, preco, tipo_medicao, categoria = product_data
                
                quantity = 1.0 # Padrão para Unidade
                
                if tipo_medicao.lower() == 'peso':
                    # Chama o diálogo de entrada de peso
                    dialog = WeightInputProductDialog(
                        product_name=nome, 
                        product_price=preco
                    )
                    
                    if dialog.exec() == QDialog.Accepted:
                        # Se aceito, pega o peso (quantidade)
                        quantity, _ = dialog.get_weight_and_total()
                    else:
                        # Usuário cancelou a entrada de peso, cancelamos a adição
                        self.search_input.clear()
                        self.search_input.setFocus()
                        return
                
                # Se for unidade, a quantity continua 1.0. Se for peso, quantity é o peso inserido.
                
                # 5. ADICIONA O ITEM AO CARRINHO
                # O CartManager deve ser adaptado para CALCULAR O TOTAL (preco * quantity)
                self.cart_manager.add_item(
                    product_data, 
                    quantity=quantity 
                )
                
                self.search_input.clear()
                total = self.cart_manager.calculate_total()
                self._update_total_display(total)
                self._update_cart_table() 
            
            else:
                # Se não encontrou nada
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
    
    def _show_selection_dialog(self, matching_products: list):
        """
        Chama o diálogo de seleção de produto para resolver a ambiguidade 
        e retorna a tupla do produto escolhido.
        """
        dialog = ProductSelectionDialog(matching_products, parent=self)
        
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_selected_product()
        else:
            return None




    def _calculate_subtotal(self):
        """
        CALCULA O SUBTOTAL BRUTO DA VENDA.
        Deve somar o (Preço Unitário * Quantidade) DE CADA ITEM no carrinho.
        Nota: Se você aplica desconto por item no CartManager, este método deve
        somar o 'total_liquido_item' de cada item.
        """
        subtotal = 0.0
        # Assumimos que cart_items_for_stock (do CartManager) contém o campo 'total_liquido_item'
        for item in self.cart_manager.cart_items:
            # Se você já aplica desconto por item no CartManager, use 'total_liquido_item'
            subtotal += item.get('total_liquido_item', item['quantidade'] * item['preco'])
        return subtotal

    def _get_cart_items_data(self):
        """
        Prepara a lista de itens do carrinho em formato de dicionário
        para ser salvo pelo VendasController.
        """
        # Garante que os itens tenham os campos de desconto/líquido que o Controller espera.
        # O CartManager deve fornecer esses campos.
        return [
            {
                'codigo': item['codigo'],
                'nome': item['nome'],
                'quantidade': item['quantidade'],
                'preco_unitario': item['preco'],
                'desconto_item': item.get('desconto_item', 0.0), # Novo Campo
                'total_liquido_item': item.get('total_liquido_item', item['quantidade'] * item['preco']) # Novo Campo
            }
            for item in self.cart_manager.cart_items
        ]

    def _handle_finalize_sale(self):
        """
        Coordena a finalização da venda, incluindo cálculo de desconto/taxa, 
        gestão de pagamentos mistos e chamada da transação no VendasController.
        """
        
        # --- 1. CÁLCULO DOS TOTAIS DA VENDA ---
        subtotal = self._calculate_subtotal()
        
        if subtotal <= 0:
            QMessageBox.warning(self, "Aviso", "Carrinho está vazio ou total é zero. Venda não finalizada.")
            return
            
        desconto = self.total_discount_value
        taxa = self.service_fee_value
        
        valor_liquido = subtotal - desconto + taxa 
        
        if valor_liquido < 0:
            QMessageBox.critical(self, "Erro", "O valor líquido não pode ser negativo. Revise o desconto.")
            return

        # --- 2. CHAMADA DO DIÁLOGO DE PAGAMENTO MISTO ---
        checkout_dialog = CheckoutDialog(
            subtotal_bruto=subtotal,
            total_liquido=valor_liquido,
            total_discount_value=desconto,
            total_service_fee=taxa,
            parent=self
        )
        
        if checkout_dialog.exec() == QDialog.Accepted:
            # --- 3. PREPARAÇÃO DOS DADOS PARA O CONTROLLER ---
            
            id_funcionario = self.logged_user.get('id')
            vendedor_nome = self.logged_user.get('nome')
            troco_recebido = checkout_dialog.troco # Leitura do troco antes de resetar
            
            if not id_funcionario or not vendedor_nome:
                QMessageBox.critical(self, "Erro", "Dados do funcionário logado incompletos. Venda não registrada.")
                return

            # 3.1. Dados da Venda Principal (Vendas)
            venda_data = {
                'id_funcionario': id_funcionario,
                'vendedor_nome': vendedor_nome,
                'valor_bruto': subtotal,
                'desconto_aplicado': desconto,
                'taxa_servico': taxa,
                'total_venda': valor_liquido,
                'valor_recebido': checkout_dialog.payment_model.get_total_paid(),
                'troco': troco_recebido
            }
            
            # 3.2. Itens do Carrinho (ItensVenda)
            itens_carrinho = self._get_cart_items_data()
            
            # 3.3. Pagamentos (PagamentosVenda)
            pagamentos = checkout_dialog.payments_list
            
            # --- 4. CHAMADA DA TRANSAÇÃO CENTRALIZADA ---
            # ⚠️ ASSUMINDO que o controller retorna: success, estoque_alerts, id_venda
            try:
                success, estoque_alerts, id_venda = self.vendas_controller.finalizar_venda_transacao(
                    venda_data, 
                    itens_carrinho, 
                    pagamentos
                )
            except Exception as e:
                QMessageBox.critical(self, "Erro de Comunicação", f"Erro inesperado no Controller: {e}")
                return
            
            # --- 5. PROCESSAMENTO DO RESULTADO ---
            if success:
                # ⭐️ SALVA OS DADOS NO CONTROLLER PARA ACESSO POSTERIOR ⭐️
                self.vendas_controller.last_venda_data = venda_data
                self.vendas_controller.last_itens_carrinho = itens_carrinho
                self.vendas_controller.last_pagamentos = pagamentos
                            
                # 5.1. Alertas de Estoque e Troco
                alert_msg = ""
                if estoque_alerts:
                    alert_msg += "Alertas de Estoque:\n" + "\n".join(estoque_alerts)
                    QMessageBox.warning(self, "Venda Concluída com Alertas", alert_msg)
                
                troco_formatado = self._format_currency(troco_recebido)
                
                # 5.2. ⭐️ CHAMADA DO NOVO DIÁLOGO DE PÓS-VENDA ⭐️
                post_sale_dialog = PostSaleDialog(
                    sale_id=id_venda, 
                    total_pago=venda_data['valor_recebido'],
                    parent=self
                )
                
                # Executa o diálogo de opções (Recibo/NF)
                if post_sale_dialog.exec() == QDialog.Accepted:
                    action = post_sale_dialog.result_action
                    
                    if action == PostSaleDialog.PRINT_RECEIPT:
                        self._print_receipt(post_sale_dialog.sale_id)
                    elif action == PostSaleDialog.PRINT_INVOICE:
                        self._print_invoice(post_sale_dialog.sale_id)
                
                # 5.3. Exibe o Troco (se houver, após as opções de impressão)
                if troco_recebido > 0:
                    QMessageBox.information(self, "Sucesso & Troco", f"Troco para o cliente: {troco_formatado}", QMessageBox.StandardButton.Ok)

                # 5.4. Limpar a Interface
                self._reset_cart()
                
            else:
                # O Controller já registrou o erro no console/log.
                QMessageBox.critical(self, "Erro de Transação", 
                                    "Falha ao registrar a venda. A transação foi desfeita. Verifique o log e tente novamente.")

    # --- FIM DO MÉTODO _handle_finalize_sale ---
            
    
    def _handle_total_discount_dialog(self):
        """Abre um diálogo para aplicar desconto/acréscimo no total da venda."""
        
        # 1. Obtenha o subtotal atual do carrinho
        subtotal = self._calculate_subtotal() # Você precisará criar este método
        
        # 2. Instancie e exiba o novo diálogo de desconto
        discount_dialog = TotalDiscountDialog(subtotal, parent=self)
        if discount_dialog.exec():
            # Após fechar o diálogo, recupere o valor de desconto/acréscimo aplicado
            self.total_discount_value = discount_dialog.final_discount_value
            self.service_fee_value = discount_dialog.final_service_fee_value
            
            # Recalcular e atualizar o display do total (R$ 0,00)
            self._update_total_display()
        
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

    # ui/main_window.py (dentro da classe PDVWindow)

    def _setup_cart_model(self):
        """Configura o Modelo de dados para a QTableView."""
        self.cart_model = QStandardItemModel(0, 7) 
        self.cart_model.setHorizontalHeaderLabels(["CÓDIGO", "NOME", "PREÇO UN.", "QUANT.", "TOTAL ITEM"])
        self.cart_table.setModel(self.cart_model)
        
        # 0. CÓDIGO (Ajuste leve)
        self.cart_table.setColumnWidth(0, 100) 
        # 1. NOME (Continua a maior)
        self.cart_table.setColumnWidth(1, 300)
        # 2. PREÇO UN. (Aumentado para garantir espaço para o título)
        self.cart_table.setColumnWidth(2, 120) 
        # 3. QUANT. (Aumentado para garantir espaço para o título)
        self.cart_table.setColumnWidth(3, 100) 
        # 4. TOTAL ITEM (Aumentado levemente)
        self.cart_table.setColumnWidth(4, 120) 
        
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
        """Configura os layouts e widgets da janela, incluindo o botão de Logout."""
        
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
        
        # O método _setup_autocompleter deve ser definido na classe
        if hasattr(self, '_setup_autocompleter'):
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
        self.total_display.setObjectName("totalDisplay")
        self.total_display.setFont(QFont("Arial", 32, QFont.Bold))
        self.total_display.setAlignment(Qt.AlignCenter)
        
        checkout_layout.addWidget(QLabel("TOTAL DA VENDA:", alignment=Qt.AlignCenter))
        checkout_layout.addWidget(self.total_display)
        checkout_layout.addSpacing(40) 

        # 2. Campo de Valor Recebido (Apenas visual)
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
        
        # Botão: Relatórios de Vendas
        self.reports_button = QPushButton("📊 Relatórios de Vendas")
        self.reports_button.setFont(QFont("Arial", 12))
        self.reports_button.setStyleSheet("background-color: #3f51b5; color: white; padding: 10px; border-radius: 5px;") 
        self.reports_button.clicked.connect(self._show_sales_reports) 
        checkout_layout.addWidget(self.reports_button)
        
        # Botão: Gerenciar Produtos
        self.manage_products_button = QPushButton("📦 Gerenciar Produtos")
        self.manage_products_button.setFont(QFont("Arial", 12))
        self.manage_products_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 5px;") 
        self.manage_products_button.clicked.connect(self._show_product_management)
        checkout_layout.addWidget(self.manage_products_button) 
        
        # Botão: Cadastrar Funcionário
        self.register_employee_button = QPushButton("👨‍💼 Cadastrar Funcionário")
        self.register_employee_button.setFont(QFont("Arial", 12))
        self.register_employee_button.setStyleSheet("background-color: #FF5722; color: white; padding: 10px; border-radius: 5px;") 
        self.register_employee_button.clicked.connect(self._show_employee_registration)
        checkout_layout.addWidget(self.register_employee_button)
        
        # Botão: Gerenciar Funcionários (Listar, Editar, Excluir)
        self.manage_employee_button = QPushButton("👥 Gerenciar Funcionários")
        self.manage_employee_button.setFont(QFont("Arial", 12))
        self.manage_employee_button.setStyleSheet("background-color: #03A9F4; color: white; padding: 10px; border-radius: 5px;") 
        self.manage_employee_button.clicked.connect(self._show_employee_management)
        checkout_layout.addWidget(self.manage_employee_button)
        
        # ----------------------------------------------------------------------
        # ⭐️ BOTÃO DE LOGOUT ADICIONADO AQUI ⭐️
        self.logout_button = QPushButton("🚪 SAIR (Logout)") 
        self.logout_button.setFont(QFont("Arial", 12))
        self.logout_button.setStyleSheet("background-color: #F44336; color: white; padding: 10px; border-radius: 5px;") 
        self.logout_button.clicked.connect(self._handle_logout)
        checkout_layout.addWidget(self.logout_button)
        # ----------------------------------------------------------------------
        
        is_admin = self.logged_user['cargo'] == 'admin'

        if not is_admin:
            
            # 1. BLOQUEIO DE FUNCIONÁRIOS
            self.register_employee_button.setVisible(False)
            self.register_employee_button.setEnabled(False)
            self.manage_employee_button.setVisible(False) 
            self.manage_employee_button.setEnabled(False)
            
            # 2. BLOQUEIO DE GERENCIAMENTO DE PRODUTOS
            register_button.setVisible(False)
            register_button.setEnabled(False)
            self.manage_products_button.setVisible(False)
            self.manage_products_button.setEnabled(False)
            
            # 3. BLOQUEIO DE RELATÓRIOS GERAIS
            # (Mantido visível para vendedor, filtragem interna)
            pass 
            
        # 4. Botão Finalizar (VISÍVEL para todos)
        finalize_button = QPushButton("FINALIZAR VENDA (F12)")
        finalize_button.setFont(QFont("Arial", 18, QFont.Bold))
        finalize_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px;")
        finalize_button.clicked.connect(self._handle_finalize_sale)

        checkout_layout.addWidget(finalize_button)
        checkout_layout.addStretch(1) 
        
        main_layout.addWidget(checkout_panel, 2) 

        self.setCentralWidget(central_widget)
        self.search_input.setFocus()
        
     
        # 6. ATALHO F3: Desconto/Acréscimo no Total (Checkout)
        self.shortcut_f3 = QShortcut(QKeySequence("F3"), self)
        # Supondo que você terá um método para abrir o diálogo de desconto no total
        self.shortcut_f3.activated.connect(self._handle_total_discount_dialog)
     

        # Colocar dentro da CLASSE PDVWindow:

    def _handle_logout(self):
        """Lida com a confirmação e o processo de logout."""
       # Certifique-se de que QMessageBox está importado no topo

        reply = QMessageBox.question(self, 
                                    "Confirmação de Logout", 
                                    "Tem certeza que deseja encerrar a sessão e voltar para o Login?", 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.close()
    
    def _show_employee_management(self):
        """
        Abre o diálogo de gerenciamento de funcionários.
        Passa a conexão com o banco de dados.
        """
        dialog = GerenciarFuncionariosDialog(self.db_connection, self)
        dialog.exec()
        
  # ui/main_window.py (dentro da classe PDVWindow)

# ... (após _show_employee_management ou similar)

    def _handle_open_registration(self):
        """Abre a janela de cadastro de produtos."""
        # Note: Você precisará garantir que 'ProductRegistrationWindow' está importado!
        from ui.product_registration import ProductRegistrationWindow
        self.registration_window = ProductRegistrationWindow(self.db_connection)
        self.registration_window.exec()

    def _handle_open_product_list(self):
        """Abre a janela de consulta e listagem de produtos."""
        # Note: Você precisará garantir que 'ProductListWindow' está importado!
        from ui.product_list import ProductListWindow
        self.list_window = ProductListWindow(self.db_connection)
        self.list_window.exec()
    
# ... (antes de _setup_ui)

    def _show_sales_reports(self):
    
        vendedor_logado_nome = self.logged_user.get('nome')
        is_admin = self.logged_user.get('cargo') == 'admin'

        if is_admin:
            # 1. Administrador: Passa None para ver tudo
            filtro_vendedor = None 
        else:
            # 2. Vendedor Comum: Passa o nome para filtrar
            filtro_vendedor = vendedor_logado_nome
            
            # ⭐️ AJUSTE CRÍTICO AQUI:
            # Garanta que o nome existe antes de prosseguir
            if not filtro_vendedor:
                QMessageBox.critical(self, "Erro", "Nome do funcionário logado não encontrado. Relatório indisponível.")
                return

        dialog = RelatoriosVendasDialog(
            self.db_connection, 
            # Passa o filtro, que será None (Admin) ou o nome (Vendedor)
            vendedor_logado=filtro_vendedor, 
            parent=self
        )
        dialog.exec()

    def _show_print_dialog(self, venda_id, total, recebido, troco, itens_venda):
        """
        Mostra um diálogo perguntando se o usuário deseja imprimir o recibo.
        Se Sim, chama o método de geração/impressão.
        """
        formatted_troco = f"R$ {troco:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        
        # 1. Mostrar o Troco e a pergunta
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Venda Concluída")
        msg_box.setText(f"Venda {venda_id} concluída com sucesso!\n\nTroco: **{formatted_troco}**")
        
        # Adicionar a pergunta sobre o recibo
        msg_box.setInformativeText("Deseja imprimir o recibo desta transação?")
        
        # Configurar botões: Sim (Imprimir) e Não (Apenas Fechar)
        print_button = msg_box.addButton("Sim, Imprimir Recibo", QMessageBox.YesRole)
        close_button = msg_box.addButton("Não, Apenas Fechar", QMessageBox.NoRole)
        msg_box.setDefaultButton(close_button)

        # Remove o stylesheet da Message Box para evitar problemas de visualização
        msg_box.setStyleSheet("")
        
        msg_box.exec()
        
        if msg_box.clickedButton() == print_button:
            # 2. Se o usuário escolher imprimir, chama a função de geração de recibo
            self._generate_and_print_receipt(venda_id, total, recebido, troco, itens_venda)
            
    import datetime # Certifique-se de que isso está importado no seu arquivo

    def _generate_and_print_receipt(self, venda_id, total, recebido, troco, itens_venda):
        """
        Gera o texto do recibo, incluindo a formatação 'kg' para produtos por peso.
        """
        
        vendedor = self.logged_user['nome']
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Garante que os floats sejam formatados corretamente para o padrão brasileiro no final
        def format_br(value):
            # Corrigido: usa o padrão de formatação de moeda brasileira (R$ 1.000,00)
            return f"{value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

        recibo_texto = f"""
    ========================================
        RECIBO DE VENDA - PDV
    ========================================
    Venda ID: {venda_id}
    Data/Hora: {data_hora}
    Vendedor: {vendedor}
    ----------------------------------------
    PRODUTO            QTD    PREÇO UN.   SUBTOTAL
    ----------------------------------------"""

        # ⭐️ CORREÇÃO ESSENCIAL: Desempacotamento da tupla de 5 elementos ⭐️
        # O 'itens_venda' agora é uma lista de (codigo, nome, qtd, preco, tipo_medicao)
        for codigo, nome, qtd, preco, tipo_medicao in itens_venda: 
            
            subtotal = qtd * preco
            
            # 2. Lógica para formatar a Quantidade (QTD)
            if tipo_medicao.lower() == 'peso':
                # Usa 3 casas decimais e anexa " kg" para peso
                qtd_formatada = f"{qtd:7.3f} kg" 
            else:
                # Usa 2 casas decimais para unidades
                qtd_formatada = f"{qtd:10.2f}" 

            # 3. Formatação da Linha
            # Nome (largura 17), QTD (largura 12, que agora inclui o 'kg'), PREÇO (largura 10), SUBTOTAL (largura 10)
            recibo_texto += (
                f"\n{nome[:17].ljust(17)} "
                f"{qtd_formatada.ljust(12)}" 
                f"{preco:10.2f} "
                f"{subtotal:10.2f}"
            )

        # ----------------------------------------

        recibo_texto += f"""
    ----------------------------------------
    TOTAL: R$ {format_br(total)}
    RECEBIDO: R$ {format_br(recebido)}
    TROCO: R$ {format_br(troco)}
    ========================================
    """

        QMessageBox.information(self, "Impressão (Simulada)", f"Recibo gerado com sucesso. O texto abaixo seria enviado para a impressora:\n\n{recibo_texto}")
# No seu MainWindow ou onde você chama o relatório:

    def open_sales_report(self):
        # Supondo que 'self.logged_in_user_name' contém o nome do vendedor
        # E que 'self.is_admin' verifica o cargo/permissão
        
        if self.is_admin:
            vendedor_filtro = None # Administrador vê todas as vendas
        else:
            vendedor_filtro = self.logged_in_user_name # Vendedor vê apenas as suas
            
        dialog = RelatoriosVendasDialog(
            db_connection=self.db_connection,
            vendedor_logado=vendedor_filtro, # ⭐️ Novo argumento ⭐️
            parent=self
        )
        dialog.exec()