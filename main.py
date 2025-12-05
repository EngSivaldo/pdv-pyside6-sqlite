# main.py

import sys
from PySide6.QtWidgets import QApplication, QDialog
# Importa a janela principal do PDV
from ui.main_window import PDVWindow 
# Importa as funções do banco de dados
from core.database import connect_db, create_and_populate_tables 
# Importa o novo Diálogo de Login
from ui.login_dialog import LoginDialog 

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    # 1. Conecta ao DB e inicializa as tabelas
    conn = connect_db(None) 
    if conn is None:
        sys.exit(-1)
        
    create_and_populate_tables(conn)
    
    # 2. Executa o Diálogo de Login e verifica se o usuário foi aceito
    login_dialog = LoginDialog(conn)
    
    # login_dialog.exec() retorna QDialog.Accepted (1) se o login for bem-sucedido
    if login_dialog.exec() == QDialog.Accepted:
        
        logged_user = login_dialog.user_data
        
        # 3. Cria e mostra a janela principal, passando a conexão e o usuário logado
        window = PDVWindow(conn, logged_user=logged_user) 
        window.showMaximized()
        sys.exit(app.exec())
    else:
        # Se o login for cancelado ou rejeitado, fecha a aplicação
        sys.exit(0)

if __name__ == "__main__":
    main()