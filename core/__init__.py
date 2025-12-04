def __init__(self):
        super().__init__()
        # ... (código existente) ...

        # LISTA PARA ARMAZENAR ITENS DO CARRINHO (NOVO)
        # Cada item será um dicionário: {'codigo': '1001', 'nome': 'Maçã', 'preco': 1.50, 'quantidade': 1}
        self.cart_items = [] 
        
        # Conexão com o banco de dados SQLite
        # ... (código existente) ...