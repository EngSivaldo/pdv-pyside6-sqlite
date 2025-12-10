# Arquivo: core/vendas_manager.py

import sqlite3
from typing import List, Dict, Any
from core.database import connect_db # Assumindo que você tem essa função

class VendasManager:
    """
    Gerencia o estado do carrinho de compras: adição, remoção, e cálculos de totais.
    Esta classe prepara os dados que serão passados para o VendasController (DB).
    """
    
    def __init__(self):
        self.get_db_connection = connect_db
        self.cart_items: List[Dict[str, Any]] = []
        
        # Variáveis de contexto da sessão (Injetadas pela PDVWindow)
        self.id_caixa_ativo: int = 0
        self.id_vendedor: int = 0
        self.nome_vendedor: str = ""

        # Variáveis de Totais Financeiros
        self.total_bruto: float = 0.0
        self.total_discount_value: float = 0.0 # Desconto aplicado na venda (não no item)
        self.service_fee_value: float = 0.0    # Taxa de serviço aplicada
        
    def set_sessao(self, id_caixa: int, id_vendedor: int, nome_vendedor: str):
        """Define o contexto do caixa ativo e do vendedor."""
        self.id_caixa_ativo = id_caixa
        self.id_vendedor = id_vendedor
        self.nome_vendedor = nome_vendedor

    def buscar_produto(self, codigo: str) -> Dict[str, Any] | None:
        """Busca o produto no DB por código ou SKU."""
        conn = self.get_db_connection()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        try:
            # Seleciona campos essenciais
            cursor.execute("""
                SELECT id, codigo, nome, preco_venda, estoque_atual
                FROM Produtos WHERE codigo = ?
            """, (codigo,))
            
            result = cursor.fetchone()
            if result:
                # Adapte os índices (0=id, 1=codigo, 2=nome, 3=preco_venda, 4=estoque_atual)
                return {
                    'id': result[0],
                    'codigo': result[1],
                    'nome': result[2],
                    'preco': result[3],
                    'estoque_atual': result[4],
                    'quantidade': 1.0, # Quantidade padrão
                    'desconto_item': 0.0 # Desconto inicial por item
                }
            return None
        except sqlite3.Error as e:
            print(f"Erro ao buscar produto: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_item(self, produto_data: Dict[str, Any], quantidade: float = 1.0):
        """Adiciona ou incrementa a quantidade de um item no carrinho."""
        codigo = produto_data['codigo']
        
        # Verifica se o item já está no carrinho
        for item in self.cart_items:
            if item['codigo'] == codigo:
                item['quantidade'] += quantidade
                self.recalculate_totals()
                return

        # Adiciona novo item
        produto_data['quantidade'] = quantidade
        self.cart_items.append(produto_data)
        self.recalculate_totals()

    def clear_cart(self):
        """Esvazia o carrinho e reseta os totais."""
        self.cart_items = []
        self.recalculate_totals()
        
    def calculate_total(self) -> float:
        """
        Calcula o total final da venda (líquido) após descontos e taxas.
        """
        # (Total Bruto - Desconto da Venda) + Taxa de Serviço
        total_liquido_venda = self.total_bruto - self.total_discount_value + self.service_fee_value
        return max(0.0, total_liquido_venda)

    def recalculate_totals(self):
        """Recalcula todos os totais baseados nos itens do carrinho."""
        self.total_bruto = 0.0
        
        for item in self.cart_items:
            # Calcula o valor total antes de descontos globais (Preço * Qtd)
            item_total = item['preco'] * item['quantidade']
            self.total_bruto += item_total
            
            # Nota: Descontos por item seriam aplicados aqui para calcular o total_liquido_item,
            # mas para a lógica simples, focamos no total_bruto.
            
        # Manter o desconto global e a taxa (podem ser modificados por outro método se necessário)
        # Se for necessário recalcular o total final, use calculate_total()
        
    def aplicar_desconto_global(self, percentual: float):
        """Aplica um desconto percentual sobre o total bruto."""
        if 0 <= percentual <= 100:
            desconto_valor = self.total_bruto * (percentual / 100)
            self.total_discount_value = desconto_valor
            
    # Futuros métodos: remover_item, set_quantidade, aplicar_taxa...