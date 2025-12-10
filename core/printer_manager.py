import datetime as dt
from typing import Dict, Any, List
import locale

# Tenta configurar o locale para moeda brasileira, se não conseguir, usa o padrão.
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Aviso: Não foi possível configurar o locale PT-BR. Usando formatação manual.")

class PrinterManager:
    """Gerencia a formatação de recibos e a simulação de emissão fiscal."""

    def __init__(self):
        # Você pode inicializar configurações de impressora aqui
        pass
        
    def _format_currency(self, value: float) -> str:
        """Formata um valor float para string de moeda brasileira (Ex: R$ 1.234,56)."""
        # Utiliza formatação manual para garantir compatibilidade entre sistemas
        return f"R$ {value:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

    # -----------------------------------------------------------------
    # Z. MÉTODO DE IMPRESSÃO SIMULADA
    # -----------------------------------------------------------------

    def print_text(self, content: str):
        """Simula a impressão enviando o conteúdo para o console com wrappers."""
        print("\n" + "=== INÍCIO IMPRESSÃO ===")
        print(content)
        print("=== FIM IMPRESSÃO ===" + "\n")
        
    # -----------------------------------------------------------------
    # A. RECIBO (NÃO FISCAL)
    # -----------------------------------------------------------------
    
    def generate_receipt_content(self, venda_data: Dict[str, Any], itens_carrinho: List[Dict[str, Any]], pagamentos: List[Dict[str, Any]]) -> str:
        """Gera o conteúdo de um recibo simples formatado em texto."""
        
        # Dados do cabeçalho
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
            
            # Formatação de QTD e Valores para BR
            qtd_str = f"{item['quantidade']:<5.2f}".replace('.', ',')
            vl_un_str = f"{item['preco_unitario']:>8.2f}".replace('.', ',')
            total_item_str = f"{total_item:>8.2f}".replace('.', ',')
            
            itens_str += f"{qtd_str} {nome:<20} {vl_un_str} {total_item_str}\n"

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
            pagamentos_str += f" {p['method']:<15}: {self._format_currency(p['value']):>15}\n"

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
        """Simula a chamada de uma API externa para emissão de NF-e/NFC-e."""
        
        nf_log = f"--- INÍCIO DA EMISSÃO NF-e/NFC-e ---\n"
        nf_log += f"Venda ID: {venda_data['id']}\n"
        nf_log += f"Total: {self._format_currency(venda_data['total_venda'])}\n"
        nf_log += f"Status: REQUISIÇÃO ENVIADA (SIMULAÇÃO)\n"
        nf_log += f"Necessário: Certificado Digital, NCM dos produtos e API SEFAZ.\n"
        nf_log += "--- FIM DA SIMULAÇÃO ---\n"
        
        return nf_log

    # -----------------------------------------------------------------
    # C. FECHAMENTO DE CAIXA
    # -----------------------------------------------------------------

    def format_fechamento(self, resumo: dict) -> str:
        """Formata o resumo de fechamento de caixa para impressão."""
        
        # Formatação de moeda (usando o método auxiliar)
        esperado = self._format_currency(resumo['valor_esperado'])
        declarado = self._format_currency(resumo['valor_declarado'])
        
        # Diferença absoluta para exibição
        diferenca_abs = self._format_currency(abs(resumo['diferenca'])) 
        
        # Determinar status e se é falta ou sobra
        if resumo['diferenca'] > 0.001:
            status_line = f"SOBRA: {diferenca_abs}"
            status_text = "SOBRA REGISTRADA"
        elif resumo['diferenca'] < -0.001:
            status_line = f"FALTA: {diferenca_abs}"
            status_text = "FALTA REGISTRADA"
        else:
            status_line = "OK: R$ 0,00"
            status_text = "FECHAMENTO PERFEITO"

        saida = [
            "=== COMPROVANTE DE FECHAMENTO ===",
            "========================================",
            f"CAIXA ID: {resumo['id_caixa']} - VENDEDOR: {resumo['vendedor_nome']}",
            f"ABERTURA: {resumo['data_abertura']}",
            f"FECHAMENTO: {resumo['data_fechamento']}",
            "----------------------------------------",
            f"FUNDO DE TROCO: {self._format_currency(resumo['valor_abertura'])}",
            f"TOTAL DE VENDAS: {self._format_currency(resumo['total_vendas'])}",
            "----------------------------------------",
            f"VALOR ESPERADO (Sistema): {esperado}",
            f"VALOR DECLARADO (Contado): {declarado}",
            "----------------------------------------",
            f"DIFERENÇA: {status_line}",
            "========================================",
            f"STATUS DO CAIXA: {status_text}",
            "========================================",
        ]
        return "\n".join(saida)

    def print_caixa_fechamento(self, resumo: dict):
        """Gera e envia o recibo de fechamento para a impressora (simulado no console)."""
        
        texto_recibo = self.format_fechamento(resumo)
        
        # ⭐️ CORREÇÃO: Usar o método de simulação de impressão padronizado ⭐️
        self.print_text(texto_recibo)