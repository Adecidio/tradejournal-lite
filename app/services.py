import pandas as pd
import numpy as np
from app import db
from app.models import Trade

def salvar_trades_do_excel(filepath, user):
    """
    Lê o Excel, encontra os trades e salva no Banco de Dados.
    Evita duplicatas verificando o número do Ticket.
    """
    print("--- INICIANDO PROCESSAMENTO DO EXCEL ---") # Log
    try:
        # 1. LEITURA BRUTA
        df_raw = pd.read_excel(filepath, header=None)

        # --- A. ENCONTRAR O CABEÇALHO (INÍCIO) ---
        header_index = None
        for i, row in df_raw.head(50).iterrows():
            row_text = [str(val).lower() for val in row.values]
            if any(x in row_text for x in ['position', 'ticket']) and any(x in row_text for x in ['lucro', 'profit']):
                header_index = i
                print(f"DEBUG: Cabeçalho encontrado na linha{i}")  # Log
                break

        if header_index is None:
            print("DEBUG: Cabeçalho NÃO encontrado.")
            return {"erro: " "Cabeçalho não encontrado."}
        
        # 3. O COLETOR TOLERANTE
        rows_to_keep = []

        # Começa logo após o cabeçalho
        start_row = header_index + 1
        print(f"DEBUG: Começando a varrer dados a partir da linha {start_row}")

        for i in range(start_row, len(df_raw)):
            row = df_raw.iloc[i]

            # Pega o valor da coluna Ticket (índice 1)
            raw_val = row[1]
            val_str = str(raw_val).strip()

            # A. SE FOR VAZIO -> PULA (CONTINUE), NÃO PARA!
            if pd.isna(raw_val) or val_str == "" or val_str.lower() == 'nan':
                continue

            # B. SE FOR "TOTAL" -> AÍ SIM PARA
            if "total" in val_str.lower():
                print(f"DEBUG: Parada acionada. Encontrei a palavra 'Total' na linha {i}")
                break

            # C . SE FOR TEXTO ESTRANHO
            if any(c.isalpha() for c in val_str) and not val_str.replace('.', '', 1).isdigit():
                print(f"DEBUG: Parada acionada. Encontrei texto não numérico '{val_str}' na linha {i}")
                break

            # D. TENTA CONVERTER PARA NÚMERO
            # Se passar aqui, é trade.
            try:
                float(val_str.replace(',', '.'))
                # Se deu certo, guarda a linha inteira!
                rows_to_keep.append(row)
            except ValueError:
                print(f"DEBUG: Parada por erro de conversão na linha {i}. Valor: {val_str}")
                break

        print(f"DEBUG: Total de linhas válidas coletadas: {len(rows_to_keep)}")

        if not rows_to_keep:
            return {"erro": "Nenhum trade válido encontrado."}
        
        # 4. MONTAR DATAFRAME FINAL
        df = pd.DataFrame(rows_to_keep)

        novos_nomes = [
            'time_open', 'ticket', 'symbol', 'type', 'volume', 'price_open',
            'sl', 'tp', 'time_close', 'price_close', 'commission', 'swap', 'profit'
        ]

        # Ajuste seguro de colunas
        cols_count = min(len(df.columns), 13)
        mapeamento = {i: novos_nomes[i] for i in range(cols_count)}
        df.rename(columns=mapeamento, inplace=True)

        # 5. GRAVAÇÃO DO BANCO DE DADOS
        contador_novos = 0

        for index, row in df.iterrows():
            # Limpa Ticket (tira .0)
            try:
                ticket_limpo = str(int(float(row['ticket'])))
            except:
                ticket_limpo = str(row['ticket'])

            existe = Trade.query.filter_by(user_id=user.id, ticket=ticket_limpo).first()

            if existe:
                print(f"AVISO: Ticket {ticket_limpo} já existe no banco. Ignorando.")
            else:
                # Se não existe, vamos criar!
                try:
                    dt_open = pd.to_datetime(row['time_open'], dayfirst=False, errors='coerce')
                    dt_close = pd.to_datetime(row['time_close'], dayfirst=False, errors='coerce')
                except:
                    dt_open = None
                    dt_close = None

                # Tratamento de Valoes float (troca vírgula por ponto)
                def clean_float(val):
                    try:
                        return float(str(val).replace(',', '.'))
                    except:
                        return 0.0
                    
                novo_trade = Trade(
                    user_id=user.id,
                    ticket=ticket_limpo,
                    symbol=str(row['symbol']),
                    type=str(row['type']),
                    volume=clean_float(row['volume']),
                    
                    open_time=dt_close,
                    close_time=dt_close,

                    open_price=clean_float(row['price_open']),
                    close_price=clean_float(row['price_close']),
                    sl=clean_float(row['sl']),
                    tp=clean_float(row['tp']),

                    commission=clean_float(row['commission']),
                    swap=clean_float(row['swap']),
                    profit=clean_float(row['profit']),
                )

                # Calcula o líquido
                novo_trade.net_result = novo_trade.profit + novo_trade.commission + novo_trade.swap

                # Adiciona no carrinho do banco
                db.session.add(novo_trade)
                contador_novos += 1
                print(f"SUCESSO: Ticket {ticket_limpo} adicionado à fila.")
            # Salva tudo de uma vez
            db.session.commit()
            print(f"--- FIM. NOVOS TRADES SALVOS: {contador_novos} ---")
            return {"sucesso": True, "novos_trades": contador_novos}
        

    except Exception as e:
        db.session.rollback()  # Cancela se der erro no meio
        print(f"ERRO CRÍTICO NO SERVICES: {e}")
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
            'price_open': t.open_price,
            'price_close': t.close_price,
            'net_result': t.net_result,
            'close_time': t.close_time
        })

    df = pd.DataFrame(dados_lista)

    # --- PROTEÇÃO CONTRA DADOS VAZIOS ---
    if 'close_time' in df.columns:
        df['close_time'] = pd.to_datetime(df['close_time']).fillna(pd.Timestamp('1970-01-01'))

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
    lista_patrimonio = df['net_result'].cumsum().tolist()
    lista_patrimonio.insert(0, 0)

    df_sorted = df.sort_values(by='close_time', ascending=False)
    lista_trades_recente = df_sorted.to_dict('records')

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