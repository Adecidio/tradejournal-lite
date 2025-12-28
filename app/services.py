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
        
        for i, row in df_raw.head(30).iterrows():
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

       # 3. EXTRAÇÃO CIRÚRGICA (O frieo de mão)
       # Para assim que encontra uma linha que não seja um operação
        rows_to_keep = []
        # Pega todas as linhas abaixo do cabeçalho
        candidate_rows = df_raw.iloc[header_index + 1:].values

        for row in candidate_rows:
            # Estrutura: [Horario, Ticket, Ativo...]
            ticket_val = row[1]

            # Verificação: É um número válido?
            val_str = str(ticket_val).strip()

            if val_str.replace('.', '').isdigit():
                # É um ticket numérico (ex: "123456"), então é uma linha de operação válida.
                rows_to_keep.append(row)
            else:
                # ACABOU A TABELA DE POSIÇÕES. PARA DE LER.
                break

        if not rows_to_keep:
            return {"erro:" "Tabela de Posições encontrada, mas parece estar vazia."}
        
        # 4. CRIAÇÃO DO DATAFRAME LIMPO
        # Recria o DataFrame apenas com as linhas salvas
        df = pd.DataFrame(rows_to_keep)

        # 5. RENOMEAR COLUNAS
        novos_nomes = [
            'time_open', 'ticket', 'symbol', 'type', 'volume', 'price_open',
            'sl', 'tp', 'time_close', 'price_close', 'commission', 'swap', 'profit'
        ]
        
        # Verifica se temos colunas suficientes
        if len(df.columns) < 13:
            # Se tiver menos colunas, tenta aproveitar o que tem (fallback)
            cols_to_use = min(len(df.columns), 13)
            mapeamento = {i: novos_nomes[i] for i in range(cols_to_use)}
        else:
            mapeamento = {i: novos_nomes[i] for i in range(13)}

        df.rename(columns=mapeamento, inplace=True)


        # 6. TRATAMENTO FINANCEIRO (Vírgula vs Ponto)
        cols_financeiras = ['profit', 'swap', 'commission']
        for col in cols_financeiras:
            if col in df.columns:
                # Converte para string, troca vírgula por ponto
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                # Converte para float, transformando erros em 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 7. CÁLCULO FINAL
        # Se alguma coluna faltar, assume 0
        lucro = df['profit'] if 'profit' in df.columns else 0
        swap = df['swap'] if 'swap' in df.columns else 0
        comissao = df['commission'] if 'commission' in df.columns else 0


        df['net_result'] = lucro + swap + comissao

        # Estatísticas
        total_trades = len(df)
        resultado_financeiro = df['net_result'].sum()
        maior_lucro = df['net_result'].max()
        maior_perda = df['net_result'].min()
        
        taxa_acerto = 0
        profit_factor = 0

        if total_trades > 0:
            trades_vencedores = len(df[df['net_result'] > 0])
            taxa_acerto = (trades_vencedores / total_trades) * 100
        
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