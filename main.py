# main.py

import sys
from PySide6.QtWidgets import QApplication, QDialog
from ui.main_window import PDVWindow 
from core.database import connect_db, create_and_populate_tables 
from ui.login_dialog import LoginDialog 

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    # 1. Conexão e Inicialização do DB (FORA DO LOOP)
    conn = connect_db(None) 
    if conn is None:
        sys.exit(-1)
        
    create_and_populate_tables(conn)
    
    # 2. Loop principal da Aplicação: Gerencia o fluxo Login <-> PDV
    while True:
        # --- A. DIÁLOGO DE LOGIN ---
        login_dialog = LoginDialog(conn)
        
        # login_dialog.exec() retorna QDialog.Accepted (1) se o login for bem-sucedido
        if login_dialog.exec() == QDialog.Accepted:
            
            logged_user = login_dialog.user_data
            
            # --- B. JANELA PRINCIPAL DO PDV ---
            window = PDVWindow(conn, logged_user=logged_user) 
            window.showMaximized()
            
            # Bloqueia a execução e mantém o PDV aberto.
            # O controle só volta para o loop 'while True' quando a 'window.close()' é chamada (ex: pelo botão Logout).
            app.exec()
            
            # Após o app.exec() retornar, o loop recomeça e a LoginDialog é aberta novamente.
            
        else:
            # Se o login for cancelado, a janela de login for fechada ou o app.exec() retornar
            # por um fechamento definitivo, saímos do loop e encerramos a aplicação.
            break

    # 3. Encerramento
    conn.close() # Fecha a conexão DB
    sys.exit(0)  # Encerra o aplicativo

if __name__ == "__main__":
    main()