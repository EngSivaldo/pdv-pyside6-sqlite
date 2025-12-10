# Arquivo: ui/caixa_fechamento_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QDoubleValidator, QFont

# Importa o CaixaManager para a lógica de negócios (manter import no topo)
# from core.caixa_manager import CaixaManager 

class CaixaFechamentoDialog(QDialog):
    
    # ⭐️ 1. CORREÇÃO: Adicionar printer_manager ao construtor ⭐️
    def __init__(self, caixa_manager, id_funcionario_logado: int, printer_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fechamento de Caixa")
        self.resize(500, 350) 
        
        self.caixa_manager = caixa_manager
        self.id_funcionario_logado = id_funcionario_logado
        
        # ⭐️ 2. CORREÇÃO: Salvar o printer_manager para uso posterior ⭐️
        self.printer_manager = printer_manager
        
        self.caixa_aberto_data = None # Armazenará os dados do caixa atual
        
        # Tenta carregar os dados do caixa imediatamente
        if not self._load_caixa_data():
            # Se não conseguir carregar, rejeita o diálogo imediatamente
            QMessageBox.critical(self, "Erro", "Nenhum caixa aberto encontrado para fechar.")
            self.reject()
            return

        self.setup_ui()

    # ⭐️ 3. CORREÇÃO: O método _load_caixa_data deve estar aqui (identado corretamente) ⭐️
    def _load_caixa_data(self):
        """
        Carrega os dados da sessão de caixa aberta para o funcionário logado.
        """
        self.caixa_aberto_data = self.caixa_manager.get_caixa_aberto(self.id_funcionario_logado)
        return self.caixa_aberto_data is not None

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("💰 Fechar Sessão de Caixa")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Layout de Formulário para exibir os detalhes
        form_layout = QFormLayout()
        
        # Detalhes do Caixa 
        self.valor_abertura = self.caixa_aberto_data.get('valor_abertura', 0.0)
        
        form_layout.addRow(QLabel("ID do Caixa:"), QLabel(f"<b>{self.caixa_aberto_data['id']}</b>"))
        form_layout.addRow(QLabel("Aberto em:"), QLabel(self.caixa_aberto_data.get('data_abertura', 'N/D')))
        form_layout.addRow(QLabel("Fundo de Troco (R$):"), QLabel(f"<b>{self.valor_abertura:,.2f}</b>"))
        
        # INPUT DO VALOR DECLARADO
        self.valor_fechamento_input = QLineEdit() # NOME CORRETO DA VARIÁVEL
        self.valor_fechamento_input.setPlaceholderText("0,00")
        self.valor_fechamento_input.setFont(QFont("Arial", 12))
        
        # Configurar validador
        validator = QDoubleValidator(0.00, 99999.99, 2)
        validator.setLocale(QLocale(QLocale.Portuguese, QLocale.Brazil)) 
        self.valor_fechamento_input.setValidator(validator)
        
        # Sugerir o fundo de troco (formatado corretamente para exibição)
        formatted_value = f"{self.valor_abertura:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        self.valor_fechamento_input.setText(formatted_value) 
        self.valor_fechamento_input.selectAll()
        
        form_layout.addRow(QLabel("Valor Declarado (R$):"), self.valor_fechamento_input)
        
        main_layout.addLayout(form_layout)
        
        # --- Botões ---
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        close_button = QPushButton("Fechar Caixa")
        close_button.setFont(QFont("Arial", 10, QFont.Bold))
        close_button.clicked.connect(self.handle_fechar_caixa)
        close_button.setDefault(True)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
    def get_valor_fechamento(self):
        """Retorna o valor declarado de fechamento como float, tratando o formato local."""
        try:
            # Substitui vírgula por ponto para conversão correta em Python/SQLite
            # Usa o nome de input correto
            text = self.valor_fechamento_input.text().replace(',', '.')
            return float(text)
        except ValueError:
            return 0.0

    # ⭐️ 4. CORREÇÃO: Reorganização do fluxo para evitar UnboundLocalError ⭐️
    def handle_fechar_caixa(self):
        
        # 1. OBTER E VALIDAR DADOS DE ENTRADA
        valor_declarado = self.get_valor_fechamento()
        id_caixa = self.caixa_aberto_data['id']
        
        if valor_declarado <= 0:
            QMessageBox.warning(self, "Valor Inválido", "O valor declarado para fechamento deve ser positivo.")
            self.valor_fechamento_input.setFocus()
            return
            
        # 2. CHAMAR LÓGICA DE NEGÓCIOS E ATRIBUIR RESULTADO
        resumo = self.caixa_manager.fechar_caixa(id_caixa, valor_declarado)
        
        # 3. TRATAR O RESULTADO E IMPRIMIR
        if resumo['success']:
            # Fechamento bem-sucedido.
            diferenca = resumo['diferenca']
            
            # Lógica para determinar a mensagem, ícone e status de diferença
            diferenca_abs = abs(diferenca)
            
            if diferenca_abs < 0.01:
                msg_diferenca = "O caixa fechou **exatamente** no valor esperado."
                icone = QMessageBox.Information
                status_text = 'EXATO'
            elif diferenca > 0:
                msg_diferenca = f"O caixa está **sobrando** R$ {diferenca_abs:,.2f}."
                icone = QMessageBox.Warning
                status_text = 'SOBRANDO'
            else: # diferenca < 0
                msg_diferenca = f"O caixa está **faltando** R$ {diferenca_abs:,.2f}."
                icone = QMessageBox.Warning
                status_text = 'FALTANDO'
            
            # Exibe o resumo
            QMessageBox(
                icone,
                "Caixa Fechado com Sucesso", 
                f"Sessão ID: {id_caixa}\n"
                f"Valor Esperado: R$ {resumo['valor_esperado']:,.2f}\n"
                f"Valor Declarado: R$ {resumo['valor_declarado']:,.2f}\n"
                f"Diferença: {msg_diferenca}",
                QMessageBox.StandardButton.Ok
            ).exec()
            
            # Perguntar sobre a impressão
            print_question = QMessageBox.question(
                self, 
                "Imprimir Recibo", 
                "Gostaria de imprimir o comprovante de fechamento de caixa?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if print_question == QMessageBox.StandardButton.Yes:
                # Chama a função de impressão (self.printer_manager agora está definido)
                self.printer_manager.print_caixa_fechamento(resumo) 
                
            self.accept() # Fecha o diálogo
            
        else:
            # Fechamento com falha (mensagem vinda do CaixaManager)
            QMessageBox.critical(self, "Erro no Fechamento", resumo['message'])