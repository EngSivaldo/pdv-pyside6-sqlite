# core/cart_logic.py - VERSÃO CORRIGIDA E FINALIZADA

class CartManager:
    """Gerencia a lista de itens no carrinho, os cálculos de total e a manipulação (adição/remoção)."""
    
    def __init__(self):
        self.cart_items = []

    # ALTERAÇÃO PRINCIPAL: Adicionado o parâmetro 'quantity' (padrão 1.0)
    def add_item(self, product_data: tuple, quantity: float = 1.0):
        """Adiciona ou incrementa um item no carrinho com a quantidade especificada."""
        codigo, nome, preco, tipo = product_data[:4] 
        
        found_in_cart = False
        for item in self.cart_items:
            if item['codigo'] == codigo:
                item['quantidade'] += quantity
                found_in_cart = True
                break
        
        if not found_in_cart:
            self.cart_items.append({
                'codigo': codigo, 
                'nome': nome, 
                'preco': preco, 
                'quantidade': quantity,
                'tipo': tipo
            })
            
    def remove_item(self, codigo: str):
        """
        CORRIGIDO: Remove o item **inteiro** do carrinho, independentemente da quantidade.
        Isto é mais seguro para um atalho (F4) em PDV, especialmente com itens por peso.
        """
        
        # Cria uma nova lista que exclui o item com o código correspondente
        original_length = len(self.cart_items)
        self.cart_items = [item for item in self.cart_items if item['codigo'] != codigo]
        
        if len(self.cart_items) < original_length:
            print(f"LOG: Item com código {codigo} removido do carrinho.")
        else:
            print(f"AVISO: Código {codigo} não encontrado no carrinho para remoção.")


    def calculate_total(self) -> float:
        """Calcula a soma total dos itens no carrinho (preço * quantidade)."""
        return sum(item['preco'] * item['quantidade'] for item in self.cart_items)

    def clear_cart(self):
        """Limpa o carrinho após finalizar a venda."""
        self.cart_items = []
        
    def update_quantity(self, codigo: str, nova_quantidade: float):
        """Atualiza a quantidade de um item no carrinho. Remove o item se a nova quantidade for <= 0."""
        if nova_quantidade <= 0:
            # Se a nova quantidade for zero ou negativa, remove o item
            self.cart_items = [item for item in self.cart_items if item['codigo'] != codigo]
            return

        for item in self.cart_items:
            if item['codigo'] == codigo:
                # O item['quantidade'] deve ser float para pesos
                item['quantidade'] = float(nova_quantidade) 
                break