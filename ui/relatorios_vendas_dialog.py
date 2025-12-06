import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QHeaderView, QMessageBox, 
    QHBoxLayout, QLabel, QPushButton, QDateEdit
)
from PySide6.QtSql import QSqlQueryModel, QSqlDatabase, QSqlQuery
from PySide6.QtCore import Qt, QModelIndex, QDate
from PySide6.QtGui import QFont

class RelatoriosVendasDialog(QDialog):
    """Diálogo para exibir o histórico de vendas e seus detalhes, com filtros de data e vendedor."""

    # ⭐️ NOVO PARÂMETRO: vendedor_logado ⭐️
    def __init__(self, db_connection, vendedor_logado=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico e Relatórios de Vendas")
        self.db_connection = db_connection
        # self.vendedor_logado será o nome do vendedor (str) ou None (se for admin)
        self.vendedor_logado = vendedor_logado 
        self.resize(1100, 700)
        
        self.setup_db_connection()
        self.setup_ui()
        self.load_sales_history() # Carrega o histórico inicial
        
    def setup_db_connection(self):
        """Configura a conexão QtSql separada para uso com QSqlQueryModel."""
        try:
            # Obtém o caminho do arquivo do SQLite a partir da conexão padrão
            cursor = self.db_connection.cursor()
            # Esta PRAGMA retorna o caminho do arquivo para a primeira (main) database
            cursor.execute("PRAGMA database_list") 
            db_path = cursor.fetchone()[2] 
        except Exception as e:
            QMessageBox.critical(self, "Erro DB", f"Não foi possível obter o caminho do DB: {e}")
            self.reject()
            return
        
        # Cria uma conexão única para o modelo de relatório
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

        # ⭐️ AJUSTE: Rótulo de Cabeçalho indicando o filtro ⭐️
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
        
        apply_button = QPushButton("Aplicar Filtro")
        apply_button.setFont(QFont("Arial", 11, QFont.Bold))
        apply_button.clicked.connect(self.load_sales_history)
        filter_layout.addWidget(apply_button)
        
        filter_layout.addStretch(1)
        main_layout.addLayout(filter_layout)

        # --- 2. Totais e Fechar ---
        totals_layout = QHBoxLayout()
        self.total_sales_label = QLabel("Total de Vendas Exibidas: R$ 0.00")
        self.total_sales_label.setFont(QFont("Arial", 14, QFont.Bold))
        totals_layout.addWidget(self.total_sales_label)
        
        totals_layout.addStretch(1)
        
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        totals_layout.addWidget(close_button)
        
        main_layout.addLayout(totals_layout)
        
        # --- 3. Tabela de Histórico de Vendas ---
        main_layout.addWidget(QLabel(header_text)) # Usa o novo rótulo
        self.sales_table_view = QTableView()
        self.sales_table_view.setSelectionBehavior(QTableView.SelectRows)
        self.sales_table_view.setSelectionMode(QTableView.SingleSelection)
        self.sales_table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.sales_table_view.clicked.connect(self.show_sale_details) 
        main_layout.addWidget(self.sales_table_view)

        # --- 4. Tabela de Detalhes da Venda Selecionada ---
        main_layout.addWidget(QLabel("Detalhes da Venda Selecionada (Itens):"))
        self.details_table_view = QTableView()
        self.details_table_view.setFixedHeight(180)
        self.details_table_view.setEditTriggers(QTableView.NoEditTriggers)
        main_layout.addWidget(self.details_table_view)
        
    def load_sales_history(self):
        """Carrega o histórico de vendas para a tabela principal, aplicando filtro de datas E de vendedor (se não for admin)."""
        
        if not self.qt_db.isOpen():
            QMessageBox.critical(self, "Erro DB", "Conexão Qt DB não está aberta.")
            return

        # Obter e formatar as datas
        start_date = self.date_start_input.date().toString("yyyy-MM-dd 00:00:00")
        end_date = self.date_end_input.date().toString("yyyy-MM-dd 23:59:59")
        
        self.model = QSqlQueryModel(self)
        
        # Base da Query
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
        
        # ⭐️ AJUSTE CRÍTICO: FILTRO SEGURO PARA VENDEDOR ⭐️
        if self.vendedor_logado:
            # Se self.vendedor_logado tem um valor, significa que não é admin e precisa de filtro.
            # Adiciona o placeholder nomeado à query
            base_query += " AND F.nome = :vendedor_nome"
            
        # Finaliza a Query
        base_query += " ORDER BY V.data_hora DESC"
        
        query = QSqlQuery(self.qt_db)
        query.prepare(base_query)
        
        # Faz o BIND dos valores de data
        query.bindValue(":start_date", start_date)
        query.bindValue(":end_date", end_date)
        
        # Faz o BIND do nome do vendedor, se o filtro estiver ativo
        if self.vendedor_logado:
            query.bindValue(":vendedor_nome", self.vendedor_logado)
        
        if not query.exec():
            QMessageBox.critical(self, "Erro de Query", f"Erro ao executar filtro: {query.lastError().text()}")
            return
            
        self.model.setQuery(query)
            
        # 4. Configuração da Tabela e Cabeçalhos (inalterada)
        self.model.setHeaderData(0, Qt.Horizontal, "ID Venda")
        self.model.setHeaderData(1, Qt.Horizontal, "Data/Hora")
        self.model.setHeaderData(2, Qt.Horizontal, "Vendedor")
        self.model.setHeaderData(3, Qt.Horizontal, "Total (R$)")
        self.model.setHeaderData(4, Qt.Horizontal, "Recebido (R$)")
        self.model.setHeaderData(5, Qt.Horizontal, "Troco (R$)")

        self.sales_table_view.setModel(self.model)
        
        self.sales_table_view.hideColumn(0) 
        self.sales_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.sales_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) 
        
        self._calculate_total_sales()
        
        if self.model.rowCount() == 0:
            QMessageBox.information(self, "Relatório", "Nenhuma venda encontrada no período selecionado.")


    def _calculate_total_sales(self):
        """Calcula e exibe o total das vendas que estão sendo exibidas na tabela."""
        total_sum = 0.0
        total_column = 3 # Coluna 'Total (R$)'
        
        for row in range(self.model.rowCount()):
            index = self.model.index(row, total_column)
            value = self.model.data(index)
            if value is not None:
                try:
                    total_sum += float(value)
                except (ValueError, TypeError):
                    continue

        self.total_sales_label.setText(f"Total de Vendas Exibidas: R$ {total_sum:.2f}")

    def show_sale_details(self, index: QModelIndex):
        """Carrega os itens da venda selecionada na tabela de detalhes."""
        # Garante que o details_model exista
        if not hasattr(self, 'details_model'):
            self.details_model = QSqlQueryModel(self)
            
        if not index.isValid():
            # Limpa os detalhes se nada estiver selecionado
            # Cria um QSqlQueryModel vazio para limpar o view
            self.details_table_view.setModel(QSqlQueryModel(self)) 
            return

        # 1. Obtém o 'venda_id' da linha selecionada (coluna 0)
        venda_id_index = self.model.index(index.row(), 0)
        venda_id = self.model.data(venda_id_index)
        
        if venda_id is None: return

        # 2. Query para buscar os itens da venda específica
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
            
        # 3. Configura os cabeçalhos da tabela de detalhes
        self.details_model.setHeaderData(0, Qt.Horizontal, "Produto")
        self.details_model.setHeaderData(1, Qt.Horizontal, "Qtd.")
        self.details_model.setHeaderData(2, Qt.Horizontal, "Preço Unit. (R$)")
        self.details_model.setHeaderData(3, Qt.Horizontal, "Subtotal (R$)")

        # Ajusta a largura das colunas
        self.details_table_view.setModel(self.details_model)
        self.details_table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.details_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.details_table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.details_table_view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)