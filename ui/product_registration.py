import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QDoubleSpinBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Mapeamento de prefixos para categorias (Mantido para geração de código)
CATEGORY_PREFIXES = {
    "Alimentos": "A",
    "Bebidas": "B",
    "Limpeza": "L",
    "Higiene Pessoal": "H",
    "Eletrônicos": "E",
    "Outros": "O"
}

class ProductRegistrationWindow(QDialog):
    
    def __init__(self, db_connection, product_id=None, parent=None): 
        super().__init__(parent) 
        self.setWindowTitle("Cadastro de Produtos")
        self.setGeometry(200, 200, 450, 400) # Aumentei a altura para o novo campo
        self.db_connection = db_connection
        self.product_id = product_id 
        
        self._setup_ui()
        
        # Geração de Código e Conexão
        self._generate_next_code() 
        self.category_input.currentTextChanged.connect(self._generate_next_code) 
        
        # Lógica de Edição: Carrega os dados se o ID estiver presente
        if self.product_id is not None:
            self._load_product_data()
            self.setWindowTitle("Editar Produto")
            # Ao editar, o código não deve ser gerado ou alterado novamente
            self.code_input.setReadOnly(True)

    def _setup_ui(self):
        """Configura os campos e botões de cadastro."""
        main_layout = QVBoxLayout(self)
        
        input_font = QFont("Arial", 12)
        
        # --- Campo Código (Automático e Read-Only) ---
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("Código:"))
        self.code_input = QLineEdit()
        self.code_input.setFont(input_font)
        self.code_input.setReadOnly(True) 
        self.code_input.setStyleSheet("background-color: #f0f0f0;")
        code_layout.addWidget(self.code_input)
        main_layout.addLayout(code_layout)
        
        # --- Campo Nome ---
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nome do Produto:"))
        self.name_input = QLineEdit()
        self.name_input.setFont(input_font)
        self.name_input.setPlaceholderText("Ex: Água Mineral 500ml")
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)
        
        # --- Campo Preço ---
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Preço (R$):"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("R$ ")
        self.price_input.setDecimals(2)
        self.price_input.setRange(0.01, 99999.99)
        self.price_input.setFont(input_font)
        self.price_input.setAlignment(Qt.AlignRight)
        price_layout.addWidget(self.price_input)
        main_layout.addLayout(price_layout)
        
        # ⭐️ NOVO CAMPO: QUANTIDADE EM ESTOQUE ⭐️
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Estoque (Qtd):"))
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setDecimals(2)
        self.qty_input.setRange(0.00, 99999.99)
        self.qty_input.setFont(input_font)
        self.qty_input.setAlignment(Qt.AlignRight)
        qty_layout.addWidget(self.qty_input)
        main_layout.addLayout(qty_layout)
        
        # --- Campo: Categoria ---
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Categoria:"))
        self.category_input = QComboBox() 
        self.category_input.setFont(input_font)
        self.category_input.addItems(list(CATEGORY_PREFIXES.keys()))
        self.category_input.setCurrentText("Alimentos")
        category_layout.addWidget(self.category_input)
        main_layout.addLayout(category_layout)
        
        # --- Campo: Tipo de Medição ---
        sale_type_layout = QHBoxLayout()
        sale_type_layout.addWidget(QLabel("Método de Venda:"))
        self.sale_type_input = QComboBox() 
        self.sale_type_input.setFont(input_font)
        self.sale_type_input.addItems(["Unidade", "Peso"]) # Corresponde à tipo_medicao
        self.sale_type_input.setCurrentText("Unidade")
        sale_type_layout.addWidget(self.sale_type_input)
        main_layout.addLayout(sale_type_layout)
        
        main_layout.addStretch(1)
        
        # --- Botões ---
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("💾 Salvar Produto")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        save_button.clicked.connect(self._handle_save_product)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.setFont(QFont("Arial", 12))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)

    def _generate_next_code(self):
        """Gera o próximo código sequencial baseado na categoria selecionada."""
        selected_category = self.category_input.currentText() 
        prefix = CATEGORY_PREFIXES.get(selected_category, "X")
        
        if not self.db_connection: return

        # Somente gera novo código se NÃO estiver em modo edição
        if self.product_id is not None:
             return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT codigo FROM Produtos 
                WHERE codigo LIKE ? 
                ORDER BY codigo DESC 
                LIMIT 1
            """, (f'{prefix}%',))
            
            last_code = cursor.fetchone()

            next_number = 1
            if last_code:
                last_code_str = last_code[0]
                try:
                    number_part = last_code_str[len(prefix):]
                    last_number = int(number_part)
                    next_number = last_number + 1
                except ValueError:
                    next_number = 1
            
            new_code = f"{prefix}{next_number:03d}" 
            self.code_input.setText(new_code)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de BD", f"Erro ao gerar código: {e}")
            self.code_input.setText("ERRO")

    def _insert_product(self, codigo, nome, preco, quantidade, tipo_medicao, categoria):
        """Executa a query INSERT. Retorna True/False."""
        if not self.db_connection: return False
        
        try:
            cursor = self.db_connection.cursor()
            # ⭐️ CORREÇÃO: Adicionando a coluna 'quantidade' ao INSERT ⭐️
            cursor.execute(
                "INSERT INTO Produtos (codigo, nome, preco, quantidade, tipo_medicao, categoria) VALUES (?, ?, ?, ?, ?, ?)",
                (codigo, nome, preco, quantidade, tipo_medicao, categoria) 
            )
            self.db_connection.commit()
            return True
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Erro de BD", f"O código '{codigo}' já existe no sistema. Use um código único.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de BD", f"Erro ao inserir produto: {e}")
            return False

    def _load_product_data(self):
        """
        Carrega os dados do produto usando self.product_id e preenche os campos do formulário.
        """
        self.code_input.setText(self.product_id) 
        try:
            cursor = self.db_connection.cursor()
            # ⭐️ CORREÇÃO: Adicionando a coluna 'quantidade' ao SELECT ⭐️
            query = "SELECT nome, preco, quantidade, tipo_medicao, categoria FROM Produtos WHERE codigo = ?"
            cursor.execute(query, (self.product_id,))
            
            data = cursor.fetchone()
            
            if data:
                # Ajustamos o unpack para incluir a nova coluna
                nome, preco, quantidade, tipo_medicao, categoria = data 
                
                self.name_input.setText(nome)
                self.price_input.setValue(preco) 
                self.qty_input.setValue(quantidade) # ⭐️ NOVO: Preenche a quantidade ⭐️
                self.sale_type_input.setCurrentText(tipo_medicao) 
                self.category_input.setCurrentText(categoria)

                self.setWindowTitle(f"Editar Produto: {nome}")
            else:
                QMessageBox.critical(self, "Erro de Edição", "Produto selecionado não foi encontrado.")
                self.reject() 

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro DB", f"Falha ao carregar dados do produto: {e}")
            
    def _handle_save_product(self):
        """Coleta dados, decide se deve INSERIR (Cadastro) ou ATUALIZAR (Edição)."""
        
        # 1. Coletar dados e Validar
        codigo = self.code_input.text().strip()
        nome = self.name_input.text().strip()
        preco = self.price_input.value()
        quantidade = self.qty_input.value() # ⭐️ NOVO: Coletar a quantidade ⭐️
        tipo_medicao = self.sale_type_input.currentText()
        categoria = self.category_input.currentText()
        
        if not codigo or not nome or preco <= 0:
            QMessageBox.warning(self, "Erro de Validação", "Código, Nome e Preço são obrigatórios.")
            return

        # 2. Direcionar para INSERT ou UPDATE
        if self.product_id is not None:
            # ⬅️ MODO EDIÇÃO (UPDATE)
            success = self._update_product(nome, preco, quantidade, tipo_medicao, categoria) # ⭐️ Inclui quantidade ⭐️
            title = "Edição"
        else:
            # ➡️ MODO CADASTRO (INSERT)
            success = self._insert_product(codigo, nome, preco, quantidade, tipo_medicao, categoria) # ⭐️ Inclui quantidade ⭐️
            title = "Cadastro"
            
        # 3. Status e Fechamento
        if success:
            QMessageBox.information(self, title, f"Produto salvo com sucesso! Código: {codigo}")
            
            if self.product_id is None:
                self.name_input.clear()
                self.price_input.setValue(0.01)
                self.qty_input.setValue(0.00) # Limpa o estoque para novo cadastro
                self._generate_next_code()
            else:
                self.accept()
        else:
            if title == "Edição": 
                 QMessageBox.critical(self, title, f"Erro ao salvar o produto.")


    def _update_product(self, nome, preco, quantidade, tipo_medicao, categoria):
        """
        Executa a query parametrizada UPDATE na tabela Produtos, incluindo a quantidade.
        Retorna True em caso de sucesso, False em caso de falha.
        """
        if self.product_id is None:
            QMessageBox.critical(self, "Erro Fatal", "ID do produto ausente para operação UPDATE.")
            return False

        # ⭐️ CORREÇÃO: Adicionando a coluna 'quantidade' ao UPDATE ⭐️
        query = """
            UPDATE Produtos 
            SET nome = ?, preco = ?, quantidade = ?, tipo_medicao = ?, categoria = ? 
            WHERE codigo = ?
        """
        # A ordem dos parâmetros deve corresponder à ordem dos '?' na query
        params = (nome, preco, quantidade, tipo_medicao, categoria, self.product_id)
        
        if not self.db_connection: return False

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, params)
            self.db_connection.commit()
            return True
        
        except sqlite3.Error as e:
            self.db_connection.rollback()
            QMessageBox.critical(self, "Erro de Edição DB", f"Falha na atualização do produto: {e}")
            return False