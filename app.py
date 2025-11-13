import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import linregress
import altair as alt
import os

# --- Verificação de Dependência ---
# Verifica se o openpyxl está instalado, pois é necessário para pd.read_excel
try:
    import openpyxl
except ImportError:
    st.error(
        "Erro: A biblioteca 'openpyxl' é necessária para ler os arquivos Excel."
        "Por favor, rode o comando no seu terminal: pip install openpyxl"
    )
    st.stop()

# --- Carregamento e Processamento de Dados (Otimizado com Cache) ---

@st.cache_data
def load_and_process_data():
    """
    Carrega e processa todos os 10 arquivos anuais da pasta 'base_dados'.
    Esta função é armazenada em cache pelo Streamlit para alta performance.
    """
    
    folder = "base_dados" # Nome da pasta
    years = list(range(2015, 2025)) # Anos de 2015 a 2024
    
    # Gerar a lista de nomes de arquivos
    filenames = [os.path.join(folder, f"national_M{year}_dl.xlsx") for year in years]
    
    all_dfs = []
    
    # --- 1. Carregar e Padronizar ---
    for year, filename in zip(years, filenames):
        try:
            # Lê o arquivo Excel
            df = pd.read_excel(filename) 
            df['Year'] = year
            
            # Padronizar a coluna de grupo ocupacional
            if 'O_GROUP' in df.columns:
                df = df.rename(columns={'O_GROUP': 'OCC_GROUP'})
            
            # Manter apenas as colunas necessárias
            cols_to_keep = ['Year', 'OCC_CODE', 'OCC_TITLE', 'OCC_GROUP', 'TOT_EMP']
            existing_cols = [col for col in cols_to_keep if col in df.columns]
            df_filtered = df[existing_cols]
            
            all_dfs.append(df_filtered)
            
        except FileNotFoundError:
            # Se um arquivo falhar, avisa o usuário
            raise FileNotFoundError(f"Arquivo não encontrado: {filename}. Verifique a pasta 'base_dados'.")
        except Exception as e:
            raise Exception(f"Erro ao ler {filename}: {e}")

    if not all_dfs:
        raise Exception("Nenhum dado foi carregado. A pasta 'base_dados' está vazia ou os arquivos estão nomeados incorretamente.")

    # Combinar todos os dataframes em um só
    full_data = pd.concat(all_dfs, ignore_index=True)

    # --- 2. Limpeza e Filtragem ---
    # Converter TOT_EMP para numérico. Erros (como '#' ou '*') virarão NaN (Nulo).
    full_data['TOT_EMP'] = pd.to_numeric(full_data['TOT_EMP'], errors='coerce')
    
    # Filtrar apenas por profissões de nível "detailed"
    detailed_jobs = full_data[full_data['OCC_GROUP'] == 'detailed'].copy()
    
    if detailed_jobs.empty:
        raise Exception("Nenhum dado 'detailed' encontrado. Verifique os arquivos.")

    # --- 3. Função de Regressão ---
    def calculate_slope(group):
        """
        Calcula a inclinação (slope) da Regressão Linear.
        """
        group = group.dropna(subset=['Year', 'TOT_EMP'])
        if len(group) < 2: # Precisa de pelo menos 2 pontos
            return np.nan
        
        # Converte tipos para garantir compatibilidade com linregress
        years_int = group['Year'].astype(np.int64)
        tot_emp_int = group['TOT_EMP'].astype(np.int64)
        
        result = linregress(years_int, tot_emp_int)
        return result.slope

    # --- 4. Executar Análise ---
    # Agrupar por profissão e aplicar a função de regressão
    trends = detailed_jobs.groupby('OCC_CODE').apply(calculate_slope)
    trends_df = trends.rename('slope').reset_index().dropna()

    # Buscar o nome mais recente de cada profissão para o relatório
    job_names = detailed_jobs.groupby('OCC_CODE')['OCC_TITLE'].last().reset_index()
    final_results = pd.merge(trends_df, job_names, on='OCC_CODE')

    # --- 5. Criar o Ranking ---
    final_results = final_results.sort_values(by='slope', ascending=False).reset_index(drop=True)
    final_results['Rank'] = final_results.index + 1
    final_results['Rank'] = final_results['Rank'].astype(int)

    # Retornar os dados completos (para gráficos) e os resultados (para rankings)
    return final_results, detailed_jobs

# --- Interface do Aplicativo ---

st.set_page_config(page_title="Tendências de Emprego", layout="wide")
st.title("Analisador de Tendências de Emprego (2015-2024)")

# --- Carregar Dados ---
# Tenta carregar os dados e mostra uma barra de progresso
try:
    with st.spinner("Carregando e processando 10 anos de dados... Isso pode levar um momento."):
        final_results, detailed_data = load_and_process_data()
except Exception as e:
    # Se falhar, mostra o erro e para o app
    st.error(f"Ocorreu um erro crítico ao carregar os dados: {e}")
    st.info("Verifique se a pasta 'base_dados' está no mesmo local que o 'app.py' e se todos os 10 arquivos Excel (2015-2024) estão dentro dela.")
    st.stop() # Interrompe a execução do app se os dados não puderem ser carregados

# --- Abas do App ---
tab1, tab2 = st.tabs(["Maiores Tendências", "Consultar Profissão"])

# --- Aba 1: Maiores Tendências ---
with tab1:
    st.header("Rankings de Tendência de Emprego")
    st.markdown("O 'Crescimento/Ano' é a inclinação (slope) da Regressão Linear, representando a média de empregos ganhos ou perdidos por ano.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Top 10 Profissões em Maior Alta")
        
        # Preparar dados para exibição
        top_10_display = final_results[['Rank', 'OCC_TITLE', 'slope']].head(10)
        top_10_display = top_10_display.rename(columns={'OCC_TITLE': 'Profissão', 'slope': 'Crescimento/Ano (Pessoas)'})
        # Formatar o número para melhor leitura
        top_10_display['slope_formatted'] = top_10_display['Crescimento/Ano (Pessoas)'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(
            top_10_display[['Rank', 'Profissão', 'slope_formatted']],
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("📉 Top 10 Profissões em Maior Baixa")
        
        # Pegar as 10 últimas e reordenar
        bottom_10 = final_results.tail(10)
        bottom_10_display = bottom_10[['Rank', 'OCC_TITLE', 'slope']].sort_values(by='slope', ascending=True)
        bottom_10_display = bottom_10_display.rename(columns={'OCC_TITLE': 'Profissão', 'slope': 'Crescimento/Ano (Pessoas)'})
        # Formatar o número para melhor leitura
        bottom_10_display['slope_formatted'] = bottom_10_display['Crescimento/Ano (Pessoas)'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(
            bottom_10_display[['Rank', 'Profissão', 'slope_formatted']],
            use_container_width=True,
            hide_index=True
        )

# --- Aba 2: Consultar Profissão ---
with tab2:
    st.header("Consulta Detalhada por Profissão")

    # Obter lista de todas as profissões únicas
    all_titles = final_results['OCC_TITLE'].unique()

    # --- Caixa de Busca ---
    search_term = st.text_input("Digite um nome de profissão para buscar:")

    if search_term:
        # Filtrar títulos que contêm o termo de busca (ignorando maiúsculas/minúsculas)
        matching_titles = [title for title in all_titles if search_term.lower() in title.lower()]
        if not matching_titles:
            st.warning("Nenhuma profissão encontrada com esse termo.")
            st.stop()
    else:
        # Mostrar os primeiros 100 como padrão se nada for digitado
        matching_titles = all_titles[0:100]

    # --- Caixa de Seleção ---
    selected_title = st.selectbox(
        f"Selecione a profissão ({len(matching_titles)} encontradas):",
        options=matching_titles
    )

    if selected_title:
        # --- 1. Obter Dados do Ranking ---
        job_rank_data = final_results[final_results['OCC_TITLE'] == selected_title].iloc[0]
        rank = job_rank_data['Rank']
        slope = job_rank_data['slope']
        total_jobs = len(final_results)
        
        st.divider()
        
        # Mostrar métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Classificação de Tendência",
                value=f"{rank}º",
                help=f"Classificado em {rank}º de um total de {total_jobs} profissões 'detailed'."
            )
        with col2:
            st.metric(
                label="Crescimento Médio/Ano",
                value=f"{slope:,.0f} pessoas",
                help="Baseado na inclinação da Regressão Linear (2015-2024)."
            )

        # --- 2. Preparar Dados do Gráfico ---
        occ_code = job_rank_data['OCC_CODE']
        # Buscar os dados da série temporal da profissão selecionada
        chart_data = detailed_data[detailed_data['OCC_CODE'] == occ_code]
        
        # Limpar para o gráfico
        chart_data = chart_data[['Year', 'TOT_EMP']].dropna().sort_values(by='Year')
        
        # --- 3. Criar Gráfico ---
        if chart_data.empty:
            st.warning("Não há dados de emprego suficientes para gerar um gráfico para esta profissão.")
        else:
            st.subheader(f"Histórico de Emprego: {selected_title}")
            
            # Criar o gráfico com Altair
            chart = alt.Chart(chart_data).mark_line(
                point=alt.OverlayMarkDef(color="blue", size=50) # Adiciona pontos à linha
            ).encode(
                # Usar 'Year:O' trata o ano como Categórico Ordinal, o que funciona bem
                x=alt.X('Year:O', title='Ano', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('TOT_EMP', title='Total de Empregados'),
                tooltip=[
                    alt.Tooltip('Year', title='Ano'),
                    alt.Tooltip('TOT_EMP', title='Total de Empregados', format=',')
                ]
            ).interactive() # Permite zoom e pan
            
            st.altair_chart(chart, use_container_width=True)