# core/caixa_manager.py

import sqlite3
from datetime import datetime

class CaixaManager:
    """
    Gerencia as operações de abertura, fechamento e consulta do caixa.
    Assume que 'Funcionarios' tem 'id' e 'nome', e 'Caixa' tem 'id_funcionario'.
    """
    def __init__(self, db_connection):
        # Garante que a conexão SQLite é armazenada
        self.db_connection = db_connection
        
    def caixa_aberto_exists(self, vendedor_id):
        """
        Verifica se existe um caixa com status='Aberto' para o vendedor_id.
        Este método é usado pela PDVWindow para forçar a abertura.
        Retorna True se encontrado, False caso contrário.
        """
        conn = self.db_connection
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id FROM Caixa 
                WHERE id_funcionario = ? AND status = 'Aberto'
            """, (vendedor_id,))
            
            # Se fetchone() retornar algo, significa que o caixa está aberto
            if cursor.fetchone():
                return True
            else:
                return False
                
        except sqlite3.Error as e:
            print(f"ERRO DE DB ao verificar caixa aberto (caixa_aberto_exists): {e}")
            return False
        
    def get_caixa_aberto(self, vendedor_id):
        """
        Consulta o banco de dados e retorna os dados da sessão de caixa aberta
        (Status = 'Aberto') para o VENDEDOR ESPECIFICADO.
        
        Parâmetro: vendedor_id (ID do funcionário logado)
        Retorna: Dicionário com os dados da caixa ou None.
        """
        conn = self.db_connection
        cursor = conn.cursor()
        
        # Busca a sessão de caixa aberta APENAS para o funcionário logado
        cursor.execute("""
            SELECT 
                C.id, C.valor_abertura, C.data_abertura, 
                F.nome, F.id AS id_funcionario
            FROM Caixa AS C
            JOIN Funcionarios AS F ON C.id_funcionario = F.id
            WHERE C.status = 'Aberto' AND C.id_funcionario = ?
            LIMIT 1
        """, (vendedor_id,)) 
        
        # Configura o cursor para retornar dicionários se ainda não estiver configurado
        # (Depende da sua implementação de conexão, mas vamos manter o fetchone baseado em índice)
        result = cursor.fetchone() 
        
        if result:
            caixa_data = {
                'id': result[0],
                'valor_abertura': result[1],
                'data_abertura': result[2],
                'vendedor_nome': result[3],
                'id_funcionario': result[4]
            }
            return caixa_data
        
        return None

    def abrir_caixa(self, id_funcionario: int, valor_abertura: float) -> bool:
        """
        Abre uma nova sessão de caixa com o valor inicial (fundo de troco).
        Retorna True em caso de sucesso.
        """
        # Verifica se já existe um caixa aberto para este funcionário
        # Usa get_caixa_aberto(id_funcionario) que retorna dados ou None
        if self.get_caixa_aberto(id_funcionario): 
            print("ERRO: Tentativa de abrir um novo caixa enquanto outro está ativo para este funcionário.")
            return False
            
        conn = self.db_connection
        cursor = conn.cursor()
        
        data_abertura = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute("""
                INSERT INTO Caixa (id_funcionario, data_abertura, valor_abertura, status)
                VALUES (?, ?, ?, 'Aberto')
            """, (id_funcionario, data_abertura, valor_abertura)) 
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Erro ao abrir caixa: {e}")
            return False

    # Arquivo: core/caixa_manager.py

    def fechar_caixa(self, id_caixa: int, valor_fechamento_declarado: float) -> dict:
        """
        Fecha o caixa, calcula a diferença e retorna o resumo.
        Adicionado busca por todos os metadados (datas, vendedor, etc.)
        """
        conn = self.db_connection
        cursor = conn.cursor()
        data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Obter TODOS os dados necessários: Abertura, Vendas e Dados da Sessão
        # Adicionamos F.nome (vendedor) e C.data_abertura ao SELECT principal
        cursor.execute("""
            SELECT 
                C.id, C.valor_abertura, C.data_abertura, 
                F.nome AS vendedor_nome,
                SUM(V.total_venda) AS total_vendas_liquidas
            FROM Caixa AS C
            JOIN Funcionarios AS F ON C.id_funcionario = F.id
            LEFT JOIN Vendas AS V ON V.id_caixa = C.id
            WHERE C.id = ?
            GROUP BY C.id
        """, (id_caixa,))

        result = cursor.fetchone()
        
        if not result:
            return {'success': False, 'message': 'Caixa não encontrado ou sem dados de abertura.'}
            
        # Desempacotamento dos resultados com os novos campos
        id_caixa_db, valor_abertura, data_abertura, vendedor_nome, total_vendas = result
        
        if total_vendas is None:
            total_vendas = 0.0
            
        # Se o seu valor esperado deve incluir o fundo de troco (e é o que parece estar fazendo):
        valor_esperado = valor_abertura + total_vendas 
        diferenca = valor_fechamento_declarado - valor_esperado
        
        # 2. Atualizar a tabela Caixa (O restante do código é mantido)
        try:
            cursor.execute("""
                UPDATE Caixa SET
                    data_fechamento = ?,
                    valor_fechamento_declarado = ?,
                    diferenca = ?,
                    status = 'Fechado'
                WHERE id = ? AND status = 'Aberto'
            """, (data_fechamento, valor_fechamento_declarado, diferenca, id_caixa))
            
            if cursor.rowcount == 0:
                conn.rollback()
                return {'success': False, 'message': 'Nenhum caixa aberto encontrado para o ID fornecido.'}
            
            conn.commit()
            
            # 3. Retornar Dicionário COMPLETO para a Impressão
            return {
                'success': True,
                'id_caixa': id_caixa,
                'vendedor_nome': vendedor_nome,
                'data_abertura': data_abertura,
                'data_fechamento': data_fechamento,
                'valor_abertura': valor_abertura,
                'total_vendas': total_vendas,
                'valor_esperado': valor_esperado,
                'valor_declarado': valor_fechamento_declarado,
                'diferenca': diferenca
            }
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Erro ao fechar caixa: {e}")
            return {'success': False, 'message': f'Erro de DB: {e}'}
        finally:
            # A conexão deve ser fechada onde foi aberta. Se a conexão foi passada, não feche aqui.
            # Mas mantive o seu finally por segurança:
            # if conn:
            #     conn.close() 
            pass