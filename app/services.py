import pandas as pd

def processar_relatorio(filepath):
    """
    Lê o arquivo Excel, calcula estatísticas básicas e retorna um dicionário.
    """
    try:
        # Lê o Excel usando Pandas
        df = pd.read_excel(filepath)

        # --- TRATAMENTO DE ERROS BÁSICO ---
        # Vamos assumir que o usuário vai subir um Excel com uma coluna "Profit"
        # Verifica se a coluna de lucro existe (pode ser 'Profit', 'Lucro', etc)
        colunas = [c.lower() for c in df.columns]

        if 'profit' in colunas:
            col_lucro = 'Profit'
        elif 'lucro' in colunas:
            col_lucro = 'Lucro'
        else:
            return {"erro": "Não encontrei uma coluna chamada 'Profit' ou 'Lucro' no arquivo!"}
        
        # --- CÁLCULOS (A Mágica do SaaS) ---
        total_trades = len(df)
        resultado_financeiro = df[col_lucro].sum()
        maior_lucro = df[col_lucro].max()
        maior_perda = df[col_lucro].min()

        # Conta quantos trades foram positivos (> 0)
        trades_vencedores = len(df[df[col_lucro] > 0])
        taxa_acerto = (trades_vencedores / total_trades) * 100 if total_trades > 0 else 0

        # Retorna os dados prontos para o site mostrar
        return {
            "sucesso": True,
            "total_trades": total_trades,
            "resultado_financeiro": resultado_financeiro,
            "maior_ganho": round(maior_lucro, 2),
            "maior_perda": round(maior_perda, 2),
            "taxa_acerto": round(taxa_acerto, 2)
        }

    except Exception as e:
        return {"erro": f"Erro ao processar arquivo: str{str(e)}"}
        