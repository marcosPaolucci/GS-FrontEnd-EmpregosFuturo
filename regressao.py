import pandas as pd
import numpy as np
from scipy.stats import linregress
import os # Importamos a biblioteca 'os' para juntar caminhos de pastas

def analyze_job_trends():
    """
    Carrega 10 arquivos anuais de dados de emprego (2015-2024),
    calcula a tendência de crescimento para cada profissão "detailed"
    usando Regressão Linear e exibe as 10 com maior alta.
    """

    # --- 1. Configuração dos Arquivos (Atualizado) ---
    
    folder = "base_dados" # Nome da pasta
    years = list(range(2015, 2025)) # Anos de 2015 a 2024
    
    # Gerar a lista de nomes de arquivos automaticamente
    filenames = []
    for year in years:
        filename = f"national_M{year}_dl.xlsx"
        # os.path.join junta a pasta e o nome do arquivo (ex: "base_dados/national_M2015_dl.xlsx")
        filenames.append(os.path.join(folder, filename))

    all_dfs = []

    print("Iniciando carregamento e processamento de 10 arquivos anuais...")

    # --- 2. Carregar e Padronizar os Dados (Atualizado) ---
    for year, filename in zip(years, filenames):
        try:
            # *** MUDANÇA CRÍTICA: Trocamos read_csv por read_excel ***
            df = pd.read_excel(filename) 
            
            # Adicionar a coluna de Ano
            df['Year'] = year
            
            # Padronizar a coluna de grupo ocupacional (O_GROUP em 2024, OCC_GROUP em 2015)
            if 'O_GROUP' in df.columns:
                df = df.rename(columns={'O_GROUP': 'OCC_GROUP'})
            
            # Manter apenas as colunas necessárias
            cols_to_keep = ['Year', 'OCC_CODE', 'OCC_TITLE', 'OCC_GROUP', 'TOT_EMP']
            
            # Algumas colunas podem não existir em todos os arquivos, então filtramos as que existem
            existing_cols = [col for col in cols_to_keep if col in df.columns]
            df_filtered = df[existing_cols]
            
            all_dfs.append(df_filtered)
            
        except FileNotFoundError:
            print(f"AVISO: Arquivo não encontrado para o ano {year}: {filename}")
        except Exception as e:
            print(f"Erro ao processar o arquivo {filename}: {e}")
            print("Lembrete: Se for um erro de 'engine', talvez você precise rodar 'pip install openpyxl'")

    if not all_dfs:
        print("Nenhum dado foi carregado. Verifique os nomes e caminhos dos arquivos.")
        return

    # Combinar todos os dataframes em um só
    full_data = pd.concat(all_dfs, ignore_index=True)

    # --- 3. Limpeza e Filtragem ---

    # Converter TOT_EMP para numérico. Erros (como '#' ou '*') virarão NaN (Nulo).
    full_data['TOT_EMP'] = pd.to_numeric(full_data['TOT_EMP'], errors='coerce')

    # Filtrar apenas por profissões de nível "detailed"
    # Isso remove agregados (como 'All Occupations', 'major', 'minor')
    # Usamos .copy() para evitar avisos do pandas
    detailed_jobs = full_data[full_data['OCC_GROUP'] == 'detailed'].copy()
    
    if detailed_jobs.empty:
        print("Nenhum dado de profissão 'detailed' encontrado. Verifique a coluna 'OCC_GROUP'.")
        return

    print("Dados carregados. Calculando regressão linear para cada profissão...")

    # --- 4. Função de Regressão Linear ---
    def calculate_slope(group):
        """
        Calcula a inclinação (slope) da Regressão Linear para
        TOT_EMP vs. Year.
        """
        # Remover anos com dados de emprego ausentes
        group = group.dropna(subset=['Year', 'TOT_EMP'])
        
        # Precisamos de pelo menos 2 pontos para calcular uma reta
        if len(group) < 2:
            return np.nan # Retorna Nulo se não houver dados suficientes
        
        # Realiza a regressão: Y = TOT_EMP, X = Year
        # result.slope é o 'a' da equação Y = aX + b
        # Ele representa o crescimento (ou declínio) médio por ano.
        result = linregress(group['Year'], group['TOT_EMP'])
        
        return result.slope

    # --- 5. Executar a Análise ---
    
    # Agrupar por profissão e aplicar a função de regressão
    # Isso pode levar alguns segundos
    trends = detailed_jobs.groupby('OCC_CODE').apply(calculate_slope)
    
    # Converter o resultado (Series) em um DataFrame
    trends_df = trends.rename('slope').reset_index().dropna()

    # Buscar o nome mais recente de cada profissão para o relatório
    job_names = detailed_jobs.groupby('OCC_CODE')['OCC_TITLE'].last().reset_index()

    # Juntar os resultados da tendência com os nomes
    final_results = pd.merge(trends_df, job_names, on='OCC_CODE')

    # --- 6. Exibir os Resultados ---
    
    # Ordenar pelos maiores 'slopes' (maior tendência de alta)
    top_10_growing = final_results.sort_values(by='slope', ascending=False)
    
    print("\n--- Top 10 Profissões com Maior Tendência de Alta (2015-2024) ---")
    print("O 'slope' representa o crescimento médio de empregos por ano.")
    print(top_10_growing.head(10).to_string())

# --- Para rodar o script ---
if __name__ == "__main__":
    analyze_job_trends()