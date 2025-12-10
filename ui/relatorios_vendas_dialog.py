# Importações (Atualizadas com Delegate e Locale)
import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QHeaderView, QMessageBox, 
    QHBoxLayout, QLabel, QPushButton, QDateEdit, 
    QTableWidget, QTableWidgetItem, QGroupBox, QComboBox, 
    QStyledItemDelegate # NOVO: Para criar o delegate de moeda
)
from PySide6.QtSql import QSqlQueryModel, QSqlDatabase, QSqlQuery
from PySide6.QtCore import Qt, QModelIndex, QDate, QLocale # NOVO: Para formatar moeda
from PySide6.QtGui import QFont

# ==============================================================================
# CLASSE DELEGATE PARA FORMATAR VALORES MONETÁRIOS
# ==============================================================================

class CurrencyDelegate(QStyledItemDelegate):
    """Delegate para formatar valores monetários com 2 casas decimais e alinhamento à direita."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Define a localização (pt-BR para formatação de moeda R$ 1.234,56)
        self.locale = QLocale(QLocale.Portuguese, QLocale.Brazil)

    def displayText(self, value, locale):
        """Formata o valor exibido na célula."""
        # Se o valor vier vazio do DB, retorna vazio
        if value is None or value == "":
            return ""
            
        try:
            # Tenta converter o valor para float
            number = float(value)
            # Formata como moeda (f é float, 2 é o número de casas decimais)
            # O prefixo R$ será adicionado pelo QLocale.
            return f"R$ {number:.2f}".replace('.', ',') # Força a vírgula para decimal, pois o QLocale pode usar o formato global
        except (ValueError, TypeError):
            # Retorna o valor original se não for um número válido
            return str(value)

    def createEditor(self, parent, option, index):
        # Desabilita a edição, pois é um campo de relatório
        return None

    def paint(self, painter, option, index):
        # Garante o alinhamento à direita para moedas
        option.displayAlignment = Qt.AlignRight | Qt.AlignVCenter
        super().paint(painter, option, index)

# ==============================================================================
# CLASSE PRINCIPAL DO DIÁLOGO DE RELATÓRIOS
# ==============================================================================

class RelatoriosVendasDialog(QDialog):
    
    def __init__(self, db_connection, vendedor_logado=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico e Relatórios de Vendas")
        self.db_connection = db_connection
        self.vendedor_logado = vendedor_logado 
        self.resize(1100, 700)
        
        self.setup_db_connection()
        self.setup_ui()
        
        if not self.vendedor_logado:
            self.load_vendors() 
            
        self.load_sales_history()
        self.load_vendor_totals() 

    def setup_db_connection(self):
        # [CÓDIGO INALTERADO]
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("PRAGMA database_list") 
            db_path = cursor.fetchone()[2] 
        except Exception as e:
            QMessageBox.critical(self, "Erro DB", f"Não foi possível obter o caminho do DB: {e}")
            self.reject()
            return
        
        connection_name = "sales_history_conn"
        
        if QSqlDatabase.contains(connection_name):
            self.qt_db = QSqlDatabase.database(connection_name)
        else:
            self.qt_db = QSqlDatabase.addDatabase("QSQLITE", connection_name)
            self.qt_db.setDatabaseName(db_path)
            
        if not self.qt_db.isOpen() and not self.qt_db.open():
            QMessageBox.critical(self, "Erro de Conexão DB", 
                                 f"Não foi possível abrir a conexão Qt: {self.qt_db.lastError().text()}")
            self.reject()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        input_font = QFont("Arial", 11)

        header_text = "Histórico de Transações:"
        if self.vendedor_logado:
            header_text = f"Histórico de Transações (Vendedor: {self.vendedor_logado}):"
            
        # --- 1. Filtro de Data e Ações ---
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Data Inicial:"))
        self.date_start_input = QDateEdit()
        self.date_start_input.setDate(QDate.currentDate().addMonths(-1))
        self.date_start_input.setCalendarPopup(True)
        self.date_start_input.setFont(input_font)
        filter_layout.addWidget(self.date_start_input)
        
        filter_layout.addWidget(QLabel("Data Final:"))
        self.date_end_input = QDateEdit()
        self.date_end_input.setDate(QDate.currentDate())
        self.date_end_input.setCalendarPopup(True)
        self.date_end_input.setFont(input_font)
        filter_layout.addWidget(self.date_end_input)
        
        if not self.vendedor_logado:
            filter_layout.addWidget(QLabel("Filtrar por Vendedor:"))
            self.vendor_select = QComboBox()
            self.vendor_select.setFont(input_font)
            filter_layout.addWidget(self.vendor_select)
        
        apply_button = QPushButton("Aplicar Filtro")
        apply_button.setFont(QFont("Arial", 11, QFont.Bold))
        
        apply_button.clicked.connect(self.load_sales_history)
        
        if not self.vendedor_logado:
             apply_button.clicked.connect(self.load_vendor_totals)
             
        filter_layout.addWidget(apply_button)
        
        filter_layout.addStretch(1)
        main_layout.addLayout(filter_layout)

        # --- 2. Total Geral e Botão Fechar ---
        totals_layout = QHBoxLayout()
        self.total_sales_label = QLabel("Total de Vendas Exibidas: R$ 0.00")
        self.total_sales_label.setFont(QFont("Arial", 14, QFont.Bold))
        totals_layout.addWidget(self.total_sales_label)
        
        totals_layout.addStretch(1)
        
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        totals_layout.addWidget(close_button)
        
        main_layout.addLayout(totals_layout)
        
        # --- 3. TABELA DE SUMÁRIO POR VENDEDOR ---
        
        self.totals_group = QGroupBox("📊 Total de Vendas por Vendedor (Período)")
        self.totals_layout = QVBoxLayout(self.totals_group)
        
        self.totals_table = QTableWidget()
        self.totals_table.setColumnCount(2)
        self.totals_table.setHorizontalHeaderLabels(["Vendedor", "Total Vendido (R$)"])
        self.totals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.totals_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.totals_table.setFixedHeight(120) 
        
        # Conexão para filtro de Admin
        if not self.vendedor_logado:
            self.totals_table.cellClicked.connect(self.filter_by_vendor_from_table)
            
        self.totals_layout.addWidget(self.totals_table)
        
        if not self.vendedor_logado:
            main_layout.addWidget(self.totals_group)
        
        # --- 4. Tabela de Histórico de Vendas ---
        main_layout.addWidget(QLabel(header_text)) 
        self.sales_table_view = QTableView()
        self.sales_table_view.setSelectionBehavior(QTableView.SelectRows)
        self.sales_table_view.setSelectionMode(QTableView.SingleSelection)
        self.sales_table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.sales_table_view.clicked.connect(self.show_sale_details) 
        main_layout.addWidget(self.sales_table_view)

        # --- 5. Tabela de Detalhes da Venda Selecionada ---
        main_layout.addWidget(QLabel("Detalhes da Venda Selecionada (Itens):"))
        self.details_table_view = QTableView()
        self.details_table_view.setFixedHeight(180)
        self.details_table_view.setEditTriggers(QTableView.NoEditTriggers)
        main_layout.addWidget(self.details_table_view)

    def filter_by_vendor_from_table(self, row, column):
        """
        Recebe o clique na tabela de totais (QTableWidget) e
        atualiza o QComboBox e o histórico de vendas.
        """
        if self.vendedor_logado:
            return

        vendor_item = self.totals_table.item(row, 0)
        if not vendor_item:
            return

        selected_vendor_name = vendor_item.text()
        current_filter_data = self.vendor_select.currentData()
        
        # Se o vendedor já estiver selecionado, oferece para limpar o filtro
        if current_filter_data == selected_vendor_name:
            
            reply = QMessageBox.question(self, 
                                         "Filtro Ativo",
                                         f"Atualmente, o filtro está em '{selected_vendor_name}'.\n\nDeseja reverter para 'Todos os Vendedores'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # Encontra o índice 'Todos os Vendedores' (que deve ser o índice 0)
                index_all = self.vendor_select.findData(None) 
                if index_all != -1:
                    self.vendor_select.setCurrentIndex(index_all) 
                return
            
            return # Retorna se a resposta for Não.

        # 2. Se o vendedor clicado NÃO estiver selecionado, aplica o filtro:
        index = self.vendor_select.findText(selected_vendor_name)
        
        if index != -1:
            self.vendor_select.setCurrentIndex(index)
        else:
            QMessageBox.warning(self, "Erro de Filtro", "Vendedor não encontrado na lista de filtros do sistema.")

    def load_vendors(self):
        """Carrega todos os funcionários (Admin incluso) para o QComboBox de filtro."""
        
        self.vendor_select.clear()
        self.vendor_select.addItem("Todos os Vendedores", userData=None) 
        
        query = QSqlQuery(self.qt_db)
        
        query.prepare("SELECT nome FROM Funcionarios ORDER BY nome")
        
        if not query.exec():
            QMessageBox.critical(self, "Erro de DB", f"Erro ao carregar vendedores: {query.lastError().text()}")
            return
            
        while query.next():
            nome = query.value(0)
            self.vendor_select.addItem(nome, userData=nome)
            
        # Conecta a mudança de seleção para recarregar o histórico e totais (Sem alteração)
        self.vendor_select.currentIndexChanged.connect(self.load_sales_history)
        self.vendor_select.currentIndexChanged.connect(self.load_vendor_totals)
            
    def load_sales_history(self):
        """
        Carrega o histórico de vendas na QTableView, aplicando o CurrencyDelegate
        e ajustando as larguras das colunas.
        """
        if not self.qt_db.isOpen():
            QMessageBox.critical(self, "Erro DB", "Conexão Qt DB não está aberta.")
            return

        start_date = self.date_start_input.date().toString("yyyy-MM-dd 00:00:00")
        end_date = self.date_end_input.date().toString("yyyy-MM-dd 23:59:59")
        
        filtro_vendedor_nome = self.vendedor_logado 
        
        if not filtro_vendedor_nome and hasattr(self, 'vendor_select'):
            filtro_vendedor_nome = self.vendor_select.currentData() 
        
        base_query = """
        SELECT 
            V.venda_id, 
            V.data_hora, 
            F.nome AS nome_funcionario, 
            V.total_venda,
            V.valor_recebido,
            V.troco
        FROM Vendas AS V
        LEFT JOIN Funcionarios AS F ON V.id_funcionario = F.id 
        WHERE V.data_hora BETWEEN :start_date AND :end_date
        """
        
        query = QSqlQuery(self.qt_db)
        
        if filtro_vendedor_nome:
            base_query += " AND F.nome = :vendedor_nome"
            
        base_query += " ORDER BY V.data_hora DESC"
        
        query.prepare(base_query)
        
        query.bindValue(":start_date", start_date)
        query.bindValue(":end_date", end_date)
        
        if filtro_vendedor_nome:
            query.bindValue(":vendedor_nome", filtro_vendedor_nome)
        
        if not query.exec():
            QMessageBox.critical(self, "Erro de Query", f"Erro ao executar filtro: {query.lastError().text()}")
            return
            
        self.model = QSqlQueryModel(self)
        self.model.setQuery(query)
            
        self.model.setHeaderData(0, Qt.Horizontal, "ID Venda")
        self.model.setHeaderData(1, Qt.Horizontal, "Data/Hora")
        self.model.setHeaderData(2, Qt.Horizontal, "Vendedor")
        self.model.setHeaderData(3, Qt.Horizontal, "Total (R$)")
        self.model.setHeaderData(4, Qt.Horizontal, "Recebido (R$)")
        self.model.setHeaderData(5, Qt.Horizontal, "Troco (R$)")

        self.sales_table_view.setModel(self.model)
        
        # ⭐️ NOVO: Instanciar e Aplicar o Delegate ⭐️
        currency_delegate = CurrencyDelegate(self.sales_table_view)
        
        # Colunas 3 (Total), 4 (Recebido), 5 (Troco)
        self.sales_table_view.setItemDelegateForColumn(3, currency_delegate)
        self.sales_table_view.setItemDelegateForColumn(4, currency_delegate)
        self.sales_table_view.setItemDelegateForColumn(5, currency_delegate)
        
        # ⭐️ CORREÇÃO: Ajustar a Largura das Colunas para evitar truncamento ⭐️
        self.sales_table_view.hideColumn(0) 
        
        # 1. Data/Hora (Stretch)
        self.sales_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) 
        # 2. Vendedor (ResizeToContents)
        self.sales_table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 3. Total (R$) - Largura Fixa para garantir o valor
        self.sales_table_view.setColumnWidth(3, 120) 
        # 4. Recebido (R$) - Largura Fixa
        self.sales_table_view.setColumnWidth(4, 130) 
        # 5. Troco (R$) - Largura Fixa
        self.sales_table_view.setColumnWidth(5, 130) 
        
        self._calculate_total_sales()
        
        if self.model.rowCount() == 0:
            QMessageBox.information(self, "Relatório", "Nenhuma venda encontrada no período selecionado.")

    
    def load_vendor_totals(self):
        """Calcula o total de vendas agrupado por vendedor no período e exibe na tabela de sumário."""
        
        if self.vendedor_logado or not hasattr(self, 'totals_table'):
             return
             
        start_date = self.date_start_input.date().toString("yyyy-MM-dd 00:00:00")
        end_date = self.date_end_input.date().toString("yyyy-MM-dd 23:59:59")
        
        filtro_vendedor_nome = self.vendor_select.currentData()
        
        query_text = """
            SELECT
                F.nome AS vendedor_nome,
                SUM(V.total_venda) AS total_vendido
            FROM Vendas AS V
            LEFT JOIN Funcionarios AS F ON V.id_funcionario = F.id 
            WHERE V.data_hora BETWEEN :start_date AND :end_date
        """
        
        query = QSqlQuery(self.qt_db)
        
        if filtro_vendedor_nome:
            query_text += " AND F.nome = :vendedor_nome"

        query_text += " GROUP BY F.nome ORDER BY total_vendido DESC"
        
        query.prepare(query_text)
        
        query.bindValue(":start_date", start_date)
        query.bindValue(":end_date", end_date)
        
        if filtro_vendedor_nome:
            query.bindValue(":vendedor_nome", filtro_vendedor_nome)
            
        self.totals_table.setRowCount(0)
        
        if not query.exec():
            QMessageBox.critical(self, "Erro de Query Sumário", f"Erro ao calcular totais: {query.lastError().text()}")
            return
            
        # 4. Insere os resultados na QTableWidget
        row = 0
        while query.next():
            vendedor = query.value(0)
            total = query.value(1)
            
            self.totals_table.insertRow(row)
            
            # Coluna 0: Vendedor
            item_vendedor = QTableWidgetItem(vendedor)
            self.totals_table.setItem(row, 0, item_vendedor)
            
            # Coluna 1: Total Vendido - Já formatado com f"R$ {total:.2f}"
            total_formatado = f"R$ {total:.2f}".replace('.', ',')
            item_total = QTableWidgetItem(total_formatado)
            item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.totals_table.setItem(row, 1, item_total)
            
            row += 1


    def _calculate_total_sales(self):
        # [CÓDIGO INALTERADO]
        total_sum = 0.0
        total_column = 3 
        
        for row in range(self.model.rowCount()):
            index = self.model.index(row, total_column)
            value = self.model.data(index)
            if value is not None:
                try:
                    total_sum += float(value)
                except (ValueError, TypeError):
                    continue

        self.total_sales_label.setText(f"Total de Vendas Exibidas: R$ {total_sum:.2f}".replace('.', ',')) # Substitui ponto por vírgula no total geral

    def show_sale_details(self, index: QModelIndex):
        """
        Exibe os itens da venda selecionada, aplicando o CurrencyDelegate
        à tabela de detalhes.
        """
        if not hasattr(self, 'details_model'):
            self.details_model = QSqlQueryModel(self)
            
        if not index.isValid():
            self.details_table_view.setModel(QSqlQueryModel(self)) 
            return

        venda_id_index = self.model.index(index.row(), 0)
        venda_id = self.model.data(venda_id_index)
        
        if venda_id is None: return

        details_query = QSqlQuery(self.qt_db)
        details_query.prepare("""
        SELECT 
            nome_produto, 
            quantidade, 
            preco_unitario, 
            (quantidade * preco_unitario) AS subtotal
        FROM ItensVenda
        WHERE venda_id = :venda_id
        """)
        details_query.bindValue(":venda_id", venda_id)

        if not details_query.exec():
            QMessageBox.critical(self, "Erro de Query Detalhes", f"Erro ao carregar detalhes: {details_query.lastError().text()}")
            return
            
        self.details_model.setQuery(details_query)
            
        self.details_model.setHeaderData(0, Qt.Horizontal, "Produto")
        self.details_model.setHeaderData(1, Qt.Horizontal, "Qtd.")
        self.details_model.setHeaderData(2, Qt.Horizontal, "Preço Unit. (R$)")
        self.details_model.setHeaderData(3, Qt.Horizontal, "Subtotal (R$)")

        self.details_table_view.setModel(self.details_model)
        
        # ⭐️ NOVO: Aplicar o Delegate na Tabela de Detalhes ⭐️
        currency_delegate = CurrencyDelegate(self.details_table_view)
        # Coluna 2: Preço Unit. (R$)
        self.details_table_view.setItemDelegateForColumn(2, currency_delegate) 
        # Coluna 3: Subtotal (R$)
        self.details_table_view.setItemDelegateForColumn(3, currency_delegate) 

        self.details_table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.details_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.details_table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.details_table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)