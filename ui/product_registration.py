# ui/product_registration.py

import sqlite3
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QDoubleSpinBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Mapeamento de prefixos para categorias
CATEGORY_PREFIXES = {
    "Alimentos": "A",
    "Bebidas": "B",
    "Limpeza": "L",
    "Higiene Pessoal": "H",
    "Eletrônicos": "E",
    "Outros": "O"
}

class ProductRegistrationWindow(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        self.setWindowTitle("Cadastro de Produtos")
        self.setGeometry(200, 200, 450, 300)
        self.db_connection = db_connection
        
        self._setup_ui()
        
        self._generate_next_code() 
        self.type_input.currentTextChanged.connect(self._generate_next_code)

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
        
        # --- Campo: Tipo/Categoria ---
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo/Categoria:"))
        self.type_input = QComboBox() 
        self.type_input.setFont(input_font)
        
        self.type_input.addItems(list(CATEGORY_PREFIXES.keys()))
        self.type_input.setCurrentText("Alimentos")
        type_layout.addWidget(self.type_input)
        main_layout.addLayout(type_layout)
        
        main_layout.addStretch(1)
        
        # --- Botões ---
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("💾 Salvar Produto")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        save_button.clicked.connect(self._save_product)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.setFont(QFont("Arial", 12))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)

    def _generate_next_code(self):
        """Gera o próximo código sequencial baseado no tipo de produto selecionado."""
        selected_type = self.type_input.currentText()
        prefix = CATEGORY_PREFIXES.get(selected_type, "X")
        
        if not self.db_connection: return

        try:
            cursor = self.db_connection.cursor()
            
            # Busca o código alfanumérico mais alto para o tipo selecionado
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
            
            # Formata o código: Prefixo + Número (com 3 dígitos, ex: A001)
            new_code = f"{prefix}{next_number:03d}" 
            self.code_input.setText(new_code)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de BD", f"Erro ao gerar código: {e}")
            self.code_input.setText("ERRO")

    def _save_product(self):
        """Coleta os dados, valida e insere no banco de dados."""
        codigo = self.code_input.text().strip()
        nome = self.name_input.text().strip()
        preco = self.price_input.value()
        tipo = self.type_input.currentText()
        
        if not codigo or not nome or preco <= 0:
            QMessageBox.warning(self, "Erro de Validação", "Código, Nome e Preço são obrigatórios.")
            return

        if self.db_connection:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    "INSERT INTO Produtos (codigo, nome, preco, tipo) VALUES (?, ?, ?, ?)",
                    (codigo, nome, preco, tipo)
                )
                self.db_connection.commit()
                
                QMessageBox.information(self, "Sucesso", f"Produto '{nome}' ({tipo}) cadastrado com sucesso! Código: {codigo}")
                
                # Limpa e gera o código para o próximo produto
                self.name_input.clear()
                self.price_input.setValue(0.01)
                self._generate_next_code()
                
                self.name_input.setFocus()
                
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Erro de BD", f"O código '{codigo}' já existe no sistema. Use um código único.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Erro de BD", f"Erro ao inserir produto: {e}")