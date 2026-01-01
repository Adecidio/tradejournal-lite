import pandas as pd
import numpy as np
from app import db
from app.models import Trade

def salvar_trades_do_excel(filepath, user):
    """
    Lê o Excel, encontra os trades e salva no Banco de Dados.
    Evita duplicatas verificando o número do Ticket.
    """
    try:
        # 1. LEITURA E LIMPEZA
        df_raw = pd.read_excel(filepath, header=None)

        header_index = None
        for i, row in df_raw.head(30).iterrows():
            row_text = [str(val).lower() for val in row.values]
            if any(x in row_text for x in ['position', 'ticket']) and any(x in row_text for x in ['lucro', 'profit']):
                header_index = i
                break
        if header_index is None:
            return {"erro: " "Cabeçalho não encontrado."}
        
        rows_to_keep = []
        candidate_rows = df_raw.iloc[header_index + 1:].values

        for row in candidate_rows:
            ticket_val = str(row[1]).strip()
            if ticket_val.replace('.', '').isdigit():
                rows_to_keep.append(row)
            else:
                break  # Fim da tabela

        if not rows_to_keep:
            return {"erro": "Tabela vazia."}
        
        # 2. MONTAR DATAFRAME
        df = pd.DataFrame(rows_to_keep)

        # Mapeamento de colunas (Ordem fixa do MT5)

        novos_nomes = [
            'time_open', 'ticket', 'symbol', 'type', 'volume', 'price_open',
            'sl', 'tp', 'time_close', 'price_close', 'commission', 'swap', 'profit'
        ]

        # Ajuste seguro de colunas
        cols_count = min(len(df.columns), 13)
        mapeamento = {i: novos_nomes[i] for i in range(cols_count)}
        df.rename(columns=mapeamento, inplace=True)

        # 3. GRAVAÇÃO DO BANCO DE DADOS
        contador_novos = 0

        for index, row in df.iterrows():
            ticket_atual = str(row['ticket'])

            # VERIFICAÇÃO DE DUPLICADADE:
            existe = Trade.query.filter_by(user_id=user.id, ticket=ticket_atual).first()

            if not existe:
                # Se não existe, cria o objeto Trade
                novo_trade = Trade(
                    user_id=user.id,
                    ticket=ticket_atual,
                    symbol=str(row['symbol']),
                    type=str(row['type']),
                    volume=float(str(row['volume']).replace(',', '.')),

                    # Datas (Pandas ajuda a converter)
                    open_time=pd.to_datetime(row['time_open'], dayfirst=True),
                    close_time=pd.to_datetime(row['time_close'], dayfirst=True),

                    open_price=float(str(row['price_open']).replace(',', '.')),
                    close_price=float(str(row['price_close']).replace(',', '.')),
                    sl=float(str(row['sl']).replace(',', '.')),
                    tp=float(str(row['tp']).replace(',', '.')),

                    commission=float(str(row['commission']).replace(',', '.')),
                    swap=float(str(row['swap']).replace(',', '.')),
                    profit=float(str(row['profit']).replace(',', '.')),
                )

                # Calcula o líquido
                novo_trade.net_result = novo_trade.profit + novo_trade.commission + novo_trade.swap

                # Adiciona no carrinho do banco
                db.session.add(novo_trade)
                contador_novos += 1

            # Salva tudo de uma vez
            db.session.commit()

            return {"sucesso": True, "novos_trades": contador_novos}
        

    except Exception as e:
        db.session.rollback()  # Cancela se der erro no meio
        print(f"ERRO AO SALVAR: {e}")
        return {"erro": str(e)}
    
def gerar_dados_dashboard(user):
    """
    Lê os trades DO BANCO DE DADOS e gera estatísticas para a tela.
    """
    # 1. Busca todos os trades do usuário ordenados por data de fechamento
    trades = user.trades.order_by(Trade.close_time).all()

    if not trades:
        # Retorna dados vazios se não tiver nada
        return {
            "total_trades": 0,
            "resultado_financeiro": 0,
            "maior_ganho": 0,
            "maior_perda": 0,
            "taxa_acerto": 0,
            "profit_factor": 0,
            "grafico_dados": [],
            "lista_trades": []
        }
    
    # 2. Converte Objetos do Banco para DataFrame do Pandas (para facilitar cálculos)
    dados_lista = []
    for t in trades:
        dados_lista.append({
            'ticket': t.ticket,
            'symbol': t.symbol,
            'type': t.type,
            'volume': t.volume,
            'price_open': t.price_open,
            'price_close': t.price_close,
            'net_result': t.net_result,
            'close_time': t.close_time
        })

    df = pd.DataFrame(dados_lista)

    # 3. CÁLCULOS (Iguais aos de antes)
    total_trades = len(df)
    resultado_financeiro = df['net_result'].sum()
    maior_lucro = df['net_result'].max()
    maior_prejuizo = df['net_result'].min()

    if total_trades > 0:
        trades_vencedores = len(df[df['net_result'] > 0])
        taxa_acerto = (trades_vencedores / total_trades) * 100

        soma_ganhos = df[df['net_result'] > 0]['net_result'].sum()
        soma_perdas = abs(df[df['net_result'] < 0]['net_result'].sum())
        profit_factor = round(soma_ganhos / soma_perdas, 2) if soma_perdas > 0 else 99.99
    else:
        taxa_acerto = 0
        profit_factor = 0

    # Gráfico (Soma Acumulada)
    lista_patrimonio = df['net_result'].cumsum().tolist()
    lista_patrimonio.insert(0, 0)

    # Lista de Trades (Já temos na lista de dicionários, só inverter para o mais recente primeiro)
    lista_trades_recente = df.sort_values(by='close_time', ascending=False).to_dict('records')

    return {
        "sucesso": True,
        "total_trades": int(total_trades),
        "resultado_financeiro": round(resultado_financeiro, 2),
        "maior_ganho": round(maior_lucro, 2),
        "maior_perda": round(maior_prejuizo, 2),
        "taxa_acerto": round(taxa_acerto, 2),
        "profit_factor": profit_factor,
        "grafico_dados": lista_patrimonio,
        "lista_trades": lista_trades_recente
    }