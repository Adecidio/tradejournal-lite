import pandas as pd
import numpy as np

def processar_relatorio(filepath):
    try:
        # 1. LER O ARQUIVO PULANDO O CABEÇALHO
        df = pd.read_excel(filepath, header=6)
        
        # 2. LIMPEZA INICIAL
        col_ticket = next((c for c in df.columns if 'Posi' in c), None)

        if col_ticket:
            df = df.dropna(subset=[col_ticket])

        # 3. RENOMEAR COLUNAS (Mapeamento Seguro)
        novos_nomes = [
            'time_open', 'ticket', 'symbol', 'type', 'volume', 'price_open',
            'sl', 'tp', 'time_close', 'price_close', 'commission', 'swap', 'profit'
        ]
        
        # Só renomeia se a quantidade de colunas bater
        if len(df.columns) >= 13:
            df.columns.values[:13] = novos_nomes
        else:
            return {"erro:" "O formato do Excel não parece ser o padrão 'Posições' do MT5."}
        
        # 4. TRATAMENTO DE NÚMEROS (Brasil vs EUA)
        cols_financeiras = ['profit', 'swap', 'commission']

        for col in cols_financeiras:
            # Se for texto (string), troca vírgula por ponto
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '.')
            # Converte para número (float)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 5. CÁLCULO DO RESULTADO LÍQUIDO (Net Profit)
        # Lucro Real = Lucro da Operação + Swap + Comissão
        df['net_result'] = df['profit'] + df['swap'] + df['commission']

        # 6. ESTATÍSTICAS PARA O DASHBOARD
        total_trades = len(df)
        resultado_financeiro = df['net_result'].sum()

        maior_lucro = df['net_result'].max()
        maior_perda = df['net_result'].min()

        # Contagem de Vitórias/Derrotas
        trades_vencedores = len(df[df['net_result'] > 0])
        trades_perdedores = len(df[df['net_result'] < 0]) # Ignora 0 (empate)

        taxa_acerto = (trades_vencedores / total_trades * 100) if total_trades > 0 else 0

        # --- Fator de Lucro (Profit Factor) ---
        soma_ganhos = df[df['net_result'] > 0]['net_result'].sum()
        soma_perdas = abs(df['net_result']['net_result'].sum())

        profit_factor = round(soma_ganhos / soma_perdas, 2) if soma_perdas > 0 else float('inf')

        return {
            "sucesso": True,
            "total_trades": total_trades,
            "resultado_financeiro": round(resultado_financeiro, 2),
            "maior_ganho": round(maior_lucro, 2),
            "maior_perda": round(maior_perda, 2),
            "taxa_acerto": round(taxa_acerto, 2),
            "profit_factor": profit_factor,
            "curve_data": df['net_result'].cumsum().tolist()
        }

    except Exception as e:
        print(f"ERRO DE LEITURA EXCEL: {e}")
        return {"erro": f"Erro ao processar arquivo: str{str(e)}"}
        