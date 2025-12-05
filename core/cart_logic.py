class CartManager:
    """Gerencia a lista de itens no carrinho, os cálculos de total e a manipulação (adição/remoção)."""
    
    def __init__(self):
        self.cart_items = []

    # ALTERAÇÃO PRINCIPAL: Adicionado o parâmetro 'quantity' (padrão 1.0)
    def add_item(self, product_data: tuple, quantity: float = 1.0):
        """Adiciona ou incrementa um item no carrinho com a quantidade especificada."""
        # Garantimos que 'tipo' (product_data[3]) seja lido para uso futuro, se necessário
        codigo, nome, preco, tipo = product_data[:4] 
        
        found_in_cart = False
        for item in self.cart_items:
            if item['codigo'] == codigo:
                # ALTERAÇÃO: SOMA a quantidade recebida (do diálogo ou 1.0) à existente
                item['quantidade'] += quantity
                found_in_cart = True
                break
        
        if not found_in_cart:
            self.cart_items.append({
                'codigo': codigo, 
                'nome': nome, 
                'preco': preco, 
                'quantidade': quantity, # Usa a quantidade especificada
                'tipo': tipo # Armazena o tipo para futuras lógicas (ex: interface)
            })
            
    def remove_item(self, codigo: str):
        """Diminui a quantidade de um item no carrinho ou o remove se a quantidade for 1."""
        item_found = False
        
        for i, item in enumerate(self.cart_items):
            if item['codigo'] == codigo:
                item_found = True
                
                # Para manter a lógica original: diminui 1 ou remove
                if item['quantidade'] > 1:
                    item['quantidade'] -= 1  
                    print(f"LOG: Item removido: {item['nome']}. Nova quantidade: {item['quantidade']}")
                else:
                    self.cart_items.pop(i)
                    print(f"LOG: Item removido: {item['nome']}. Item removido do carrinho.")
                break

        if not item_found:
            print(f"AVISO: Código {codigo} não encontrado no carrinho.")

    def calculate_total(self) -> float:
        """Calcula a soma total dos itens no carrinho (preço * quantidade)."""
        return sum(item['preco'] * item['quantidade'] for item in self.cart_items)

    def clear_cart(self):
        """Limpa o carrinho após finalizar a venda."""
        self.cart_items = []