# core/cart_logic.py

class CartManager:
    """Gerencia a lista de itens no carrinho, os cálculos de total e a manipulação (adição/remoção)."""
    
    def __init__(self):
        self.cart_items = []

    def add_item(self, product_data: tuple):
        """Adiciona ou incrementa um item no carrinho. Recebe a tupla do BD (codigo, nome, preco, tipo)."""
        codigo, nome, preco, tipo = product_data[:4] # Garante que pegue os 4, mesmo que 'tipo' não seja usado aqui
        
        found_in_cart = False
        for item in self.cart_items:
            if item['codigo'] == codigo:
                item['quantidade'] += 1
                found_in_cart = True
                break
        
        if not found_in_cart:
            self.cart_items.append({
                'codigo': codigo, 
                'nome': nome, 
                'preco': preco, 
                'quantidade': 1
            })
            
    def remove_item(self, codigo: str):
        """Diminui a quantidade de um item no carrinho ou o remove se a quantidade for 1."""
        item_found = False
        
        for i, item in enumerate(self.cart_items):
            if item['codigo'] == codigo:
                item_found = True
                
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