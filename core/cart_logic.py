class CartManager:
    """Gerencia a lista de itens no carrinho, os cálculos de total e a manipulação (adição/remoção)."""
    
    # ⭐️ AQUI ESTÁ A MUDANÇA ESSENCIAL ⭐️
    # ⭐️ AQUI ESTÁ A MUDANÇA ESSENCIAL ⭐️
    def __init__(self, db_connection): 
        self.cart_items = []
        
        # ⭐️ NOVO ATRIBUTO: Salva a conexão para uso futuro ⭐️
        self.db_connection = db_connection 
        
        # Inicialização dos descontos/taxas para calculate_final_total
        self.total_discount_value = 0.0
        self.service_fee_value = 0.0
        
    def add_item(self, product_data: tuple, quantity: float = 1.0):
        """
        Adiciona ou incrementa um item no carrinho. Soma apenas se for "Unidade".
        product_data: (codigo, nome, preco, tipo_medicao, ...)
        """
        # A tupla product_data vem da busca: (codigo, nome, preco, tipo_medicao, categoria)
        codigo, nome, preco, tipo_medicao = product_data[:4] 
        
        # 1. Tenta encontrar item, MAS SÓ SOMA SE FOR UNIDADE
        found_and_summed = False
        
        if tipo_medicao.lower() == 'unidade':
            for i, item in enumerate(self.cart_items):
                # Usamos o código para identificar se já está no carrinho
                if item['codigo'] == codigo: 
                    self.cart_items[i]['quantidade'] += quantity
                    found_and_summed = True
                    break
        
        # 2. SE NÃO ENCONTROU OU SE FOR PESO (Deve ser uma nova linha)
        if not found_and_summed:
            # Note que 'tipo' foi renomeado para 'tipo_medicao' para consistência
            self.cart_items.append({
                'codigo': codigo, 
                'nome': nome, 
                'preco': preco, 
                'quantidade': quantity,
                'tipo_medicao': tipo_medicao
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
        # O calculate_total funciona perfeitamente, pois o total já foi calculado implicitamente
        # pela multiplicação do preco * quantidade (peso ou unidade)
        return sum(item['preco'] * item['quantidade'] for item in self.cart_items)

    def clear_cart(self):
        """Limpa o carrinho após finalizar a venda."""
        self.cart_items = []
        
    def update_quantity(self, codigo: str, nova_quantidade: float):
        """
        Atualiza a quantidade de um item no carrinho. Remove o item se a nova quantidade for <= 0.
        Este método deve ser usado com cautela em itens por peso, pois normalmente o peso não é alterado manualmente.
        """
        if nova_quantidade <= 0:
            # Se a nova quantidade for zero ou negativa, remove o item
            self.cart_items = [item for item in self.cart_items if item['codigo'] != codigo]
            return

        for item in self.cart_items:
            if item['codigo'] == codigo:
                # O item['quantidade'] deve ser float para pesos
                item['quantidade'] = float(nova_quantidade) 
                break