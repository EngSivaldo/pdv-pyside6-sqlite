import sys
from PySide6.QtWidgets import QApplication, QDialog
# Importe Qt se precisar de flags como WA_DeleteOnClose, mas QDialog e QApplication já estão aqui.
from ui.main_window import PDVWindow 
from core.database import connect_db, create_and_populate_tables 
from ui.login_dialog import LoginDialog 

def main():
    # 1. INICIALIZAÇÃO DA APLICAÇÃO
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # ======== TEMA ========
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
    # Passa None ou o caminho do banco, dependendo da sua função connect_db
    conn = connect_db(None) 
    if conn is None:
        print("Erro fatal ao conectar no banco!")
        sys.exit(-1)

    create_and_populate_tables(conn)
    # --------------------------------

    # ======== LOOP DE LOGIN ========
    # Este loop garante que o usuário volte para o login se fechar a janela, 
    # mas não inicia o loop de eventos principal do Qt.
    
    logged_in = False
    logged_user = None

    while not logged_in:
        login_dialog = LoginDialog(conn)
        result = login_dialog.exec()

        if result == QDialog.Accepted:
            logged_user = login_dialog.user_data
            logged_in = True  # Sai do loop de login
        else:
            # Login recusado ou diálogo fechado, encerra o programa
            break 
    
    # ======== INICIALIZAÇÃO DO PDV E EXIBIÇÃO ========
    if logged_in and logged_user:
        window = PDVWindow(conn, logged_user=logged_user)
        window.showMaximized()
        
        # O programa continua a execução, mas a janela fica visível.
        # O controle de eventos é passado para app.exec() no final.
    
    # ======== FINALIZAÇÃO E LOOP DE EVENTOS PRINCIPAL ========
    
    # ⚠️ Fecha a conexão com o banco de dados.
    # Nota: Em aplicações PySide, a conexão deve ser mantida aberta se o PDV
    # ainda estiver executando. Vamos mover o close para depois do app.exec().

    # sys.exit(0)  <-- Isso será tratado pelo app.exec()
    
    # O app.exec() inicia o loop de eventos do Qt. Ele bloqueia a execução
    # até que a última janela (PDVWindow) seja fechada.
    
    exit_code = app.exec()
    
    # Se a aplicação for fechada (PDVWindow fechada), a conexão é encerrada.
    conn.close() 
    sys.exit(exit_code)


if __name__ == "__main__":
    main()