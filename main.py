# main.py

import sys
from PySide6.QtWidgets import QApplication
# Importa a janela do seu novo módulo
from ui.main_window import PDVWindow 

if __name__ == '__main__':
    # 1. Cria a instância da aplicação
    app = QApplication(sys.argv)
    
    # 2. Define o estilo padrão
    app.setStyle("Fusion") 
    
    # 3. Cria e mostra a janela principal
    window = PDVWindow()
    window.show()
    
    # 4. Inicia o loop de eventos da Qt
    sys.exit(app.exec())