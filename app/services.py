import pandas as pd
import numpy as np
from app import db
from app.models import Trade
from datetime import datetime

def salvar_trades_do_excel(filepath, user):
    print("--- INICIANDO PROCESSAMENTO (CORREÇÃO POSITION) ---")
    try:
        # 1. LEITURA BRUTA
        df_raw = pd.read_excel(filepath, header=None)
        
        # 2. ENCONTRAR O CABEÇALHO
        header_index = None
        
        # Ampliamos a busca para garantir
        for i, row in df_raw.head(50).iterrows():
            # Converte tudo para minúsculo e string para facilitar a busca
            row_text = [str(val).lower() for val in row.values]
            
            # --- AQUI ESTAVA O PROBLEMA ---
            # Adicionei 'position', 'posicoes' e 'posições' na lista
            tem_ticket = any(x in row_text for x in ['ticket', 'boleta', 'ordem', 'position', 'posicoes', 'posições'])
            tem_lucro = any(x in row_text for x in ['lucro', 'profit', 'resultado'])
            
            if tem_ticket and tem_lucro:
                header_index = i
                print(f"DEBUG: Cabeçalho encontrado na linha {i}")
                break
        
        if header_index is None:
            return {"erro": "Cabeçalho (Ticket/Position + Lucro) não encontrado."}

        # 3. COLETA DE DADOS
        rows_to_keep = []
        start_row = header_index + 1
        
        for i in range(start_row, len(df_raw)):
            row = df_raw.iloc[i]
            val_str = str(row[1]).strip() # Coluna do Ticket/Position

            # Pula vazios
            if pd.isna(row[1]) or val_str == "" or val_str.lower() == 'nan':
                continue 

            # Critérios de Parada (Fim da tabela de Posições)
            if "total" in val_str.lower():
                break
            
            # Se encontrar texto estranho (ex: cabeçalho da tabela de Ordens abaixo), para.
            # Verifica se tem letras E não é 'nan' E não é o cabeçalho 'position' de novo
            if any(c.isalpha() for c in val_str) and 'nan' not in val_str.lower():
                 # Um ajuste fino: às vezes o ticket tem letras, mas vamos assumir parada se não for numérico comum
                 # Tenta converter para float, se falhar, é texto -> para.
                 try:
                     float(val_str.replace(',', '.'))
                 except ValueError:
                     break

            # Tenta converter para número (Se passar, é trade)
            try:
                float(val_str.replace(',', '.'))
                rows_to_keep.append(row)
            except ValueError:
                continue

        if not rows_to_keep:
            return {"erro": "Nenhum trade válido encontrado."}

        # 4. PREPARAR DATAFRAME
        df = pd.DataFrame(rows_to_keep)
        
        # Mapeamento para layout padrão MT5 (13 colunas)
        # 0:TimeOpen, 1:Ticket, 2:Symbol, 3:Type, 4:Volume, 5:PriceOpen, 
        # 6:SL, 7:TP, 8:TimeClose, 9:PriceClose, 10:Comm, 11:Swap, 12:Profit
        novos_nomes = [
            'time_open', 'ticket', 'symbol', 'type', 'volume', 'price_open', 
            'sl', 'tp', 'time_close', 'price_close', 'commission', 'swap', 'profit'
        ]
        
        cols_count = min(len(df.columns), 13)
        mapeamento = {df.columns[i]: novos_nomes[i] for i in range(cols_count)}
        df.rename(columns=mapeamento, inplace=True)

        # 5. GRAVAÇÃO NO BANCO
        contador_novos = 0
        
        for index, row in df.iterrows():
            # Limpeza do Ticket
            try:
                ticket_limpo = str(int(float(row['ticket'])))
            except:
                ticket_limpo = str(row['ticket'])

            # Verifica duplicidade
            existe = Trade.query.filter_by(user_id=user.id, ticket=ticket_limpo).first()
            
            if not existe:
                try:
                    dt_open = pd.to_datetime(row['time_open'], dayfirst=False, errors='coerce')
                    dt_close = pd.to_datetime(row['time_close'], dayfirst=False, errors='coerce')
                except:
                    dt_open = None
                    dt_close = None

                def clean_float(val):
                    try:
                        return float(str(val).replace(',', '.'))
                    except:
                        return 0.0

                # Cria o objeto Trade
                novo_trade = Trade(
                    user_id=user.id,
                    ticket=ticket_limpo,
                    symbol=str(row['symbol']),
                    type=str(row['type']),
                    volume=clean_float(row['volume']),
                    open_time=dt_open,
                    close_time=dt_close,
                    open_price=clean_float(row['price_open']),
                    close_price=clean_float(row['price_close']),
                    sl=clean_float(row['sl']),
                    tp=clean_float(row['tp']),
                    commission=clean_float(row['commission']),
                    swap=clean_float(row['swap']),
                    profit=clean_float(row['profit']),
                )
                
                novo_trade.net_result = novo_trade.profit + novo_trade.commission + novo_trade.swap
                db.session.add(novo_trade)
                contador_novos += 1
        
        db.session.commit()
        return {"sucesso": True, "novos_trades": contador_novos}

    except Exception as e:
        db.session.rollback()
        print(f"ERRO CRÍTICO NO SERVICES: {e}")
        # Retorna dicionário de erro
        return {"erro": str(e)}

def gerar_dados_dashboard(user, data_inicio=None, data_fim=None):
    # 1. Começamos a query base (ainda não executada)
    query = user.trades.order_by(Trade.close_time.asc())

    # 2. Aplicamos filtros se o usuário mandou datas
    if data_inicio:
        # Filtra trades que fecharam DEPOIS ou da NA data de início
        query = query.filter(Trade.close_time >= data_inicio)

    if data_fim:
        # Filtra trades que fecharam ANTES ou NO FINAL da data de fim
        # Adicionamos o horário para pegar o dia inteiro
        data_fim_ajustada = f"{data_fim} 23:59:59"
        query = query.filter(Trade.close_time <= data_fim_ajustada)


    # 3. Executa a busca no banco
    trades = query.all()
    
    if not trades:
        return {
            "total_trades": 0, "resultado_financeiro": 0, "maior_ganho": 0,
            "maior_perda": 0, "taxa_acerto": 0, "profit_factor": 0,
            "grafico_dados": [], "lista_trades": [], "performance_ativos": []
        }

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
    
    if 'close_time' in df.columns:
        df['close_time'] = pd.to_datetime(df['close_time']).fillna(pd.Timestamp('1970-01-01'))
    
    # --- CÁLCULOS GERAIS
    total_trades = len(df)
    resultado_financeiro = df['net_result'].sum()
    maior_lucro = df['net_result'].max()
    maior_perjuizo = df['net_result'].min()
    
    if total_trades > 0:
        trades_vencedores = len(df[df['net_result'] > 0])
        taxa_acerto = (trades_vencedores / total_trades) * 100
        
        soma_ganhos = df[df['net_result'] > 0]['net_result'].sum()
        soma_perdas = abs(df[df['net_result'] < 0]['net_result'].sum())
        profit_factor = round(soma_ganhos / soma_perdas, 2) if soma_perdas > 0 else 99.99
    else:
        taxa_acerto = 0
        profit_factor = 0

    # --- PERFORMANCE POR ATIVO ---
    # Agrupa pelo símbolo e soma o resultado financeiro
    # Reset index transforma o agrupamento de volta em colunas normais
    df_ativos = df.groupby('symbol')['net_result'].sum().reset_index()

    # Ordena do maior lucro para o menor (ou maior prejuízo)
    df_ativos = df_ativos.sort_values(by='net_result', ascending=False)

    # Converte para lista de dicionários para o HTML ler
    performance_ativos = df_ativos.to_dict('records')

    # Gráfico de Curva de Patrimônio
    lista_patrimonio = df['net_result'].cumsum().tolist()
    lista_patrimonio.insert(0, 0)
    
    # Lista de Trades Detalhada
    df_sorted = df.sort_values(by='close_time', ascending=False)
    lista_trades_recente = df_sorted.to_dict('records')

    return {
        "sucesso": True,
        "total_trades": int(total_trades),
        "resultado_financeiro": round(resultado_financeiro, 2),
        "maior_ganho": round(maior_lucro, 2),
        "maior_perda": round(maior_perjuizo, 2),
        "taxa_acerto": round(taxa_acerto, 2),
        "profit_factor": profit_factor,
        "grafico_dados": lista_patrimonio,
        "lista_trades": lista_trades_recente,
        "performance_ativos": performance_ativos
    }