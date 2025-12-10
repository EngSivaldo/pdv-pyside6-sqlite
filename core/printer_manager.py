# core/printer_manager.py

import datetime as dt
from typing import Dict, Any, List

class PrinterManager:
    """Gerencia a formatação de recibos e a simulação de emissão fiscal."""

    def __init__(self):
        # Você pode inicializar configurações de impressora aqui
        pass
        
    def _format_currency(self, value: float) -> str:
        """Formata um valor float para string de moeda brasileira."""
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    # -----------------------------------------------------------------
    # A. RECIBO (NÃO FISCAL)
    # -----------------------------------------------------------------
    
    def generate_receipt_content(self, venda_data: Dict[str, Any], itens_carrinho: List[Dict[str, Any]], pagamentos: List[Dict[str, Any]]) -> str:
        """Gera o conteúdo de um recibo simples formatado em texto."""
        
        # Dados do cabeçalho (Mock-up)
        cabecalho = "========================================\n"
        cabecalho += "         NOME DA SUA EMPRESA S.A.       \n"
        cabecalho += "         Recibo Não Fiscal              \n"
        cabecalho += "========================================\n"
        cabecalho += f"CUPOM: {venda_data['id'] or 'N/A'} - Data: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        cabecalho += f"VENDEDOR: {venda_data['vendedor_nome']}\n"
        cabecalho += "----------------------------------------\n"
        
        # Itens
        itens_str = f"{'QTD':<5} {'ITEM':<20} {'VL UN':>8} {'TOTAL':>8}\n"
        
        for item in itens_carrinho:
            nome = item['nome'][:18] # Limita o nome
            total_item = item.get('total_liquido_item', item['quantidade'] * item['preco_unitario'])
            
            itens_str += f"{item['quantidade']:<5.2f} {nome:<20} {item['preco_unitario']:>8.2f} {total_item:>8.2f}\n"

        itens_str += "----------------------------------------\n"

        # Totais
        totais_str = f"SUBTOTAL BRUTO: {self._format_currency(venda_data['valor_bruto']):>19}\n"
        totais_str += f"(-) DESCONTO:   {self._format_currency(venda_data['desconto_aplicado']):>19}\n"
        totais_str += f"(+) TAXA SERV.:  {self._format_currency(venda_data['taxa_servico']):>19}\n"
        totais_str += f"TOTAL LÍQUIDO:  {self._format_currency(venda_data['total_venda']):>19}\n"
        totais_str += "========================================\n"
        
        # Pagamentos
        pagamentos_str = "PAGAMENTOS:\n"
        for p in pagamentos:
            pagamentos_str += f"  {p['method']:<15}: {self._format_currency(p['value']):>15}\n"

        pagamentos_str += f"RECEBIDO:       {self._format_currency(venda_data['valor_recebido']):>19}\n"
        pagamentos_str += f"TROCO:          {self._format_currency(venda_data['troco']):>19}\n"
        pagamentos_str += "========================================\n"
        
        # Rodapé
        rodape = "     OBRIGADO E VOLTE SEMPRE!           \n"
        
        return cabecalho + itens_str + totais_str + pagamentos_str + rodape

    # -----------------------------------------------------------------
    # B. NOTA FISCAL (SIMULAÇÃO)
    # -----------------------------------------------------------------

    def initiate_invoice_emission(self, venda_data: Dict[str, Any], itens_carrinho: List[Dict[str, Any]], pagamentos: List[Dict[str, Any]]) -> str:
        """
        Simula a chamada de uma API externa para emissão de NF-e/NFC-e.
        Na vida real, este método faria uma requisição HTTP ou chamaria um binário.
        """
        
        # ⚠️ Aviso importante sobre a complexidade da NF-e ⚠️
        nf_log = f"--- INÍCIO DA EMISSÃO NF-e/NFC-e ---\n"
        nf_log += f"Venda ID: {venda_data['id']}\n"
        nf_log += f"Total: {self._format_currency(venda_data['total_venda'])}\n"
        nf_log += f"Status: REQUISIÇÃO ENVIADA (SIMULAÇÃO)\n"
        nf_log += f"Necessário: Certificado Digital, NCM dos produtos e API SEFAZ.\n"
        nf_log += "--- FIM DA SIMULAÇÃO ---\n"
        
        return nf_log
        
    def print_to_console(self, content: str):
        """Simula a impressão enviando o conteúdo para o console."""
        print("\n\n" + "=== INÍCIO IMPRESSÃO ===")
        print(content)
        print("=== FIM IMPRESSÃO ===\n\n")