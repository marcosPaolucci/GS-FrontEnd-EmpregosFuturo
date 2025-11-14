# 📈 Analisador de Tendências de Emprego (2015–2024)

### 🌐 Acesse o aplicativo online
👉 [Abrir no Streamlit Cloud](https://gs-frontend-empregosfuturo-ajyl6qkpnqe5rjazuyrodv.streamlit.app/)

---

## 🧠 Sobre o projeto
Este aplicativo interativo analisa **tendências de emprego nos Estados Unidos entre 2015 e 2024**, identificando **as profissões que mais cresceram ou diminuíram** ao longo do tempo.

Baseado em **regressão linear**, o app estima o crescimento médio anual de cada ocupação a partir de dados do Bureau of Labor Statistics (BLS).  
Ele foi projetado para ajudar pesquisadores e analistas a entenderem **como diferentes tipos de empregos evoluem** no período analisado.

---

## 🚀 Funcionalidades principais

- 📊 **Ranking interativo** das profissões com maior crescimento e maior queda.
- 🔍 **Busca por profissão** com histórico anual de emprego.
- 📈 **Visualização gráfica interativa** (Altair) mostrando a evolução de cada ocupação.
- ⚙️ **Processamento automático de 10 anos de dados (2015–2024)**.
- ⚡ **Cache inteligente** via Streamlit para alto desempenho.

---

## 🔬 Metodologia resumida

1. Carrega automaticamente 10 arquivos de dados anuais (2015–2024).  
2. Filtra apenas as ocupações detalhadas ("detailed occupations").  
3. Aplica **regressão linear** a cada ocupação para calcular a variação média anual (`slope`).  
4. Gera um **ranking ordenado** por crescimento e disponibiliza visualizações interativas.

---

## 🧩 Tecnologias utilizadas

- **Streamlit** – Interface interativa e deploy online  
- **Pandas / NumPy** – Manipulação e análise de dados  
- **SciPy (linregress)** – Cálculo da regressão linear  
- **Altair** – Visualização de séries temporais  
- **OpenPyXL** – Leitura de planilhas Excel  

---

## 👨‍💻 Autoria

| Nome                               | RM     |
|------------------------------------|--------|
| Marcos Paolucci Salamondac         | 554941 |
| Sandron Oliveira Silva             | 557172 |
| Nickolas Alexandre de Oliveira Ferraz | 558458 |


