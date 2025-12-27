import pandas as pd
import numpy as np

def processar_relatorio(filepath):
    try:
        # 1. LEITURA BRUTA (Sem cabeçalho)
        # Lê tudo como se fosse texto simples para a gente procurar a tabela
        df_raw = pd.read_excel(filepath, header=None)

        # 2. O CAÇADOR DE CABEÇALHO
        # Vamos varrer as primeiras 20 linhas procurando onde começa a tabela real
        header_index = None
        
        for i, row in df_raw.head(20).iterrows():
            # Converte a linha toda para texto minúsculo para facilitar a busca
            row_text = [str(val).lower() for val in row.values]
            
            # A linha certa do cabeçalho costuma ter "position" (ou "ticket") E "lucro" (ou "profit")
            # Adicionamos verificações para português e inglês
            tem_ticket = any(x in row_text for x in ['position', 'posi', 'ticket'])
            tem_lucro = any(x in row_text for x in ['lucro', 'profit'])
            
            if tem_ticket and tem_lucro:
                header_index = i
                break
        
        if header_index is None:
            return {"erro": "Não consegui encontrar a tabela de 'Posições' no arquivo. Verifique se é um relatório padrão do MT5."}

        # 3. RECONSTRUIR O DATAFRAME A PARTIR DA LINHA CERTA
        # Agora que sabemos onde começa (header_index), pegamos os dados dali pra baixo
        df = df_raw.iloc[header_index + 1:].copy()
        
        # Resetar o índice para ficar organizado
        df.reset_index(drop=True, inplace=True)

        # 4. RENOMEAR COLUNAS (Pela ordem física)
        # Como o MT5 tem colunas com nomes repetidos ("Horário", "Preço"),
        # nós ignoramos os nomes originais e forçamos os nossos nomes baseados na posição da coluna.
        
        # Lista baseada no padrão que você enviou:
        # 0:Horário, 1:Ticket, 2:Ativo, 3:Tipo, 4:Vol, 5:Preço, 6:SL, 7:TP, 
        # 8:Horário_Fim, 9:Preço_Fim, 10:Comissão, 11:Swap, 12:Lucro
        novos_nomes = [
            'time_open', 'ticket', 'symbol', 'type', 'volume', 'price_open', 
            'sl', 'tp', 'time_close', 'price_close', 'commission', 'swap', 'profit'
        ]
        
        # Verifica se temos colunas suficientes
        if len(df.columns) < 13:
             return {"erro": f"A tabela encontrada tem poucas colunas ({len(df.columns)}). Esperado: 13."}

        # Aplica os nomes nas primeiras 13 colunas
        mapeamento = {df.columns[i]: novos_nomes[i] for i in range(13)}
        df.rename(columns=mapeamento, inplace=True)
        
        # Se houver mais colunas (lixo à direita), nós mantemos apenas as 13 úteis
        df = df[novos_nomes]

        # 5. LIMPEZA DE DADOS (Remover linhas vazias ou totais)
        # Remove linhas onde o Ticket está vazio (geralmente rodapé ou espaços)
        df = df.dropna(subset=['ticket'])
        
        # Garante que não pegamos linhas de "Total" que o Excel às vezes coloca
        df = df[df['ticket'].astype(str).str.isnumeric()] 

        # 6. TRATAMENTO FINANCEIRO (Vírgula vs Ponto)
        cols_financeiras = ['profit', 'swap', 'commission']
        for col in cols_financeiras:
            # Converte para string, troca vírgula por ponto
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            # Converte para float, transformando erros em 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 7. CÁLCULO FINAL
        df['net_result'] = df['profit'] + df['swap'] + df['commission']

        # Estatísticas
        total_trades = len(df)
        resultado_financeiro = df['net_result'].sum()
        maior_lucro = df['net_result'].max()
        maior_perda = df['net_result'].min()
        
        if total_trades > 0:
            trades_vencedores = len(df[df['net_result'] > 0])
            taxa_acerto = (trades_vencedores / total_trades) * 100
        else:
            taxa_acerto = 0

        # Profit Factor
        soma_ganhos = df[df['net_result'] > 0]['net_result'].sum()
        soma_perdas = abs(df[df['net_result'] < 0]['net_result'].sum())
        profit_factor = round(soma_ganhos / soma_perdas, 2) if soma_perdas > 0 else 99.99

        return {
            "sucesso": True,
            "total_trades": int(total_trades),
            "resultado_financeiro": round(resultado_financeiro, 2),
            "maior_ganho": round(maior_lucro, 2),
            "maior_perda": round(maior_perda, 2),
            "taxa_acerto": round(taxa_acerto, 2),
            "profit_factor": profit_factor
        }

    except Exception as e:
        print(f"ERRO CRÍTICO NO PROCESSAMENTO: {e}")
        # Retorna o erro para vermos na tela o que houve
        return {"erro": f"Falha interna: {str(e)}"}