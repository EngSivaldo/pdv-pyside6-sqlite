# Arquivo: main.py

import sys
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox # Adicionado QMessageBox para erros fatais
from ui.main_window import PDVWindow 
from core.database import connect_db, create_and_populate_tables 
from ui.login_dialog import LoginDialog 
from core.cart_logic import CartManager 

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # ======== TEMA (Mantido inalterado) ========
    full_style = ""

    # Tenta carregar o estilo geral (styles.qss)
    try:
        with open("styles.qss", "r") as f:
            full_style += f.read()
    except FileNotFoundError:
        pass
    except Exception as e:
        pass

    # Tenta carregar o estilo específico do Login (login.qss)
    try:
        with open("login.qss", "r") as f:
            full_style += f.read()
    except FileNotFoundError:
        pass
    except Exception as e:
        pass


    # Aplica todos os estilos combinados
    if full_style:
        app.setStyleSheet(full_style)
    # FIM DO BLOCO TEMA


    # ======== BANCO DE DADOS ========
    conn = connect_db(None) 
    if conn is None:
        QMessageBox.critical(None, "Erro Fatal", "Erro fatal ao conectar no banco de dados.")
        sys.exit(-1)

    create_and_populate_tables(conn)


    # ======== LOOP DE SESSÃO / LOGIN ========
    while True:
        login_dialog = LoginDialog(conn)

        result = login_dialog.exec()

        if result == QDialog.Accepted:
            logged_user = login_dialog.user_data

            # 1. Cria o gerenciador de carrinho
            cart_manager = CartManager(conn)
            
            # 2. Cria a janela principal do PDV
            window = PDVWindow(db_connection=conn, logged_user=logged_user, cart_manager=cart_manager)
            
            # 3. Exibe a janela
            window.showMaximized()
            
            # NOTA: O fluxo de execução PULA aqui e continua na PDVWindow.
            # O __init__ da PDVWindow chama self._ensure_caixa_aberto().
            
            # 4. Inicia o loop de eventos secundário ou espera a janela fechar
            
            # A forma mais robusta é conectar o fechamento da PDVWindow a uma ação
            # Mas, por simplicidade, faremos o controle de sessão no próprio loop
            
            # Se você usar showMaximized(), a execução NÃO é bloqueada. 
            # A maneira mais fácil de bloquear e esperar a janela fechar é usar um sinal.

            # Exemplo Simples de Sessão (Assumindo que fechar a PDVWindow significa Logout)
            app.exec() # <-- Este app.exec() ainda não é ideal aqui.

            # Solução mais limpa:

            # Não use app.exec() aqui.
            # Para controlar o loop de sessão de forma robusta, vamos conectar 
            # o fechamento da PDVWindow para reiniciar o loop (sair do PDV e ir para o Login).
            
            # Se a PDVWindow fechar (por fechar o caixa ou por clique no X), 
            # o fluxo volta para o início do while True.

            # Exemplo 1: Se você quer que o PDV seja a janela principal
            # Remova app.exec() daqui e use-o no final.
            # Se a PDVWindow for fechada, saímos do 'if' e o 'while True' recomeça o Login.
            
            pass # A execução segue para o final do 'if' e recomeça o while

        else:
            # Usuário cancelou o Login
            break
            
    # ======== FIM DO LOOP ========
    conn.close()
    
    # Executa o loop de eventos principal da aplicação UMA VEZ (se ainda não tiver sido chamado)
    # Se você está no PySide6/PyQt6, o sys.exit(app.exec()) é a forma padrão.
    sys.exit(app.exec())


if __name__ == "__main__":
    main()