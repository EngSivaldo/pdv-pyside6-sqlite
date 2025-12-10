# data/vendas_controller.py

import sqlite3
import datetime as dt
from typing import List, Dict, Any, Tuple # ⭐️ Tuple importado corretamente no topo
from PySide6.QtWidgets import QMessageBox
# Importa as funções de conexão e estoque do seu core/database.py
from core.database import connect_db, update_stock_after_sale, finalizar_venda # <--- Importações cruciais

class VendasController:
    """
    Controlador de Vendas. Coordena as operações do banco de dados (DB)
    e adiciona a lógica de negócios (desconto, taxa, pagamentos mistos).
    """
    
    def __init__(self):
        self.get_db_connection = connect_db 
        self._check_and_update_tables() # Garante que as tabelas têm os novos campos
        # ⭐️ Variáveis para armazenar os dados da última venda (necessário para impressão) ⭐️
        self.last_venda_data = {}
        self.last_itens_carrinho = []
        self.last_pagamentos = []

    def _check_and_update_tables(self):
        """
        Verifica se as tabelas Vendas, ItensVenda e PagamentosVenda possuem
        os campos necessários para Desconto/Taxa e Pagamento Misto.
        Se faltarem, adiciona-os (ALTER TABLE).
        """
        conn = self.get_db_connection()
        if conn is None: return

        cursor = conn.cursor()
        
        try:
            # --- MIGRACAO VENDAS ---
            cursor.execute("PRAGMA table_info(Vendas)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'valor_bruto' not in columns:
                cursor.execute("ALTER TABLE Vendas ADD COLUMN valor_bruto REAL DEFAULT 0.0")
            if 'desconto_aplicado' not in columns:
                cursor.execute("ALTER TABLE Vendas ADD COLUMN desconto_aplicado REAL DEFAULT 0.0")
            if 'taxa_servico' not in columns:
                cursor.execute("ALTER TABLE Vendas ADD COLUMN taxa_servico REAL DEFAULT 0.0")
            
            # --- MIGRACAO ITENSVENDA ---
            cursor.execute("PRAGMA table_info(ItensVenda)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'desconto_item' not in columns:
                cursor.execute("ALTER TABLE ItensVenda ADD COLUMN desconto_item REAL DEFAULT 0.0")
            if 'total_liquido_item' not in columns:
                cursor.execute("ALTER TABLE ItensVenda ADD COLUMN total_liquido_item REAL DEFAULT 0.0")

            # --- CRIACAO PAGAMENTOSVENDA ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS PagamentosVenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venda_id INTEGER NOT NULL,
                    metodo TEXT NOT NULL,
                    valor REAL NOT NULL,
                    FOREIGN KEY (venda_id) REFERENCES Vendas(venda_id) ON DELETE CASCADE
                );
            """)
            
            conn.commit()
            print("LOG: Estrutura de Vendas atualizada com sucesso.")
            
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Erro de Migração do BD", f"Falha ao atualizar tabelas de Vendas: {e}")
        finally:
            if conn:
                conn.close()

    def finalizar_venda_transacao(self, venda_data: Dict[str, Any], itens_carrinho: List[Dict[str, Any]], pagamentos: List[Dict[str, Any]]) -> Tuple[bool, List[str], int]:
        """
        Orquestra a transação completa: registra a venda, os itens, os pagamentos e dá baixa no estoque.
        Retorna (True/False, Lista de Alertas de Estoque, ID da Venda).
        """
        venda_id = 0 
        conn = self.get_db_connection()
        
        if conn is None:
            return False, [], venda_id 

        estoque_alerts = []
        
        try:
            cursor = conn.cursor()
            
            # --- 1.1. Inserir na tabela Vendas ---
            cursor.execute("""
                INSERT INTO Vendas (
                    data_hora, total_venda, valor_recebido, troco, id_funcionario, vendedor_nome,
                    valor_bruto, desconto_aplicado, taxa_servico
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                venda_data['total_venda'],
                venda_data['valor_recebido'], 
                venda_data['troco'], 
                venda_data['id_funcionario'], 
                venda_data['vendedor_nome'],
                venda_data['valor_bruto'],
                venda_data['desconto_aplicado'],
                venda_data['taxa_servico']
            ))
            
            venda_id = cursor.lastrowid 

            if venda_id is None or venda_id == 0:
                raise Exception("Falha ao obter o ID da venda recém-inserida.")
            
            # --- 1.2. Preparar e Inserir ItensVenda ---
            itens_venda_data = [
                (
                    venda_id, 
                    item['codigo'], 
                    item['nome'], 
                    item['quantidade'], 
                    item['preco_unitario'],
                    item.get('desconto_item', 0.0),
                    item.get('total_liquido_item', item['quantidade'] * item['preco_unitario'])
                ) 
                for item in itens_carrinho
            ]
            
            cursor.executemany("""
                INSERT INTO ItensVenda (
                    venda_id, produto_codigo, nome_produto, quantidade, preco_unitario, 
                    desconto_item, total_liquido_item
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, itens_venda_data)
            
            # --- 1.3. Inserir Pagamentos (Para Pagamento Misto) ---
            pagamentos_to_insert = [
                (venda_id, p['method'], p['value']) for p in pagamentos
            ]
            
            cursor.executemany("""
                INSERT INTO PagamentosVenda (venda_id, metodo, valor)
                VALUES (?, ?, ?)
            """, pagamentos_to_insert)

            # 2. DAR BAIXA NO ESTOQUE 
            estoque_alerts = update_stock_after_sale(conn, itens_carrinho)
            
            # 3. COMMIT DA TRANSAÇÃO
            conn.commit()
            
            # ⭐️ SUCESSO: Retorna os 3 valores esperados
            return True, estoque_alerts, venda_id 

        except Exception as e:
            conn.rollback()
            print(f"Erro CRÍTICO ao finalizar transação de venda: {e}")
            
            # ⭐️ ERRO: Retorna os 3 valores esperados
            return False, [f"Falha na transação: {e}"], 0
            
        finally:
            if conn:
                conn.close()

    # ==================== MÉTODOS DE RELATÓRIO ====================

    def buscar_vendas_detalhadas(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Busca vendas e seus pagamentos, agrupadas por venda (para Relatórios)."""
        conn = self.get_db_connection()
        if conn is None: return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    v.venda_id,
                    v.data_hora,
                    v.vendedor_nome, -- Usando o nome da Vendas (evita JOIN com Funcionarios se não precisar)
                    v.valor_bruto,
                    v.desconto_aplicado,
                    v.taxa_servico,
                    v.total_venda, 
                    pv.metodo,
                    pv.valor
                FROM Vendas v
                JOIN PagamentosVenda pv ON v.venda_id = pv.venda_id
                WHERE DATE(v.data_hora) BETWEEN ? AND ?
                ORDER BY v.data_hora DESC
            """, (start_date, end_date))
            
            vendas_agrupadas = {}
            for row in cursor.fetchall():
                v_id, data, vendedor, bruto, desc, taxa, final, metodo, valor_pago = row
                
                if v_id not in vendas_agrupadas:
                    vendas_agrupadas[v_id] = {
                        'id': v_id,
                        'data': data,
                        'vendedor': vendedor,
                        'valor_bruto': bruto,
                        'desconto': desc,
                        'taxa': taxa,
                        'valor_total_final': final,
                        'pagamentos': []
                    }
                vendas_agrupadas[v_id]['pagamentos'].append({
                    'metodo': metodo,
                    'valor': valor_pago
                })
                
            return list(vendas_agrupadas.values())

        except sqlite3.Error as e:
            print(f"Erro ao buscar relatórios de venda: {e}")
            return []
        finally:
            if conn:
                conn.close()