import pandas as pd
import requests
from bs4 import BeautifulSoup
from scipy import stats 
import yfinance as yf
import streamlit as st

# função para converter valores percentuais para valores decimais
def convert_perc(value):
    return pd.to_numeric(value.replace('%','').replace('.', '').replace(',', '.'))

# mapeando colunas que possuem valores percentuais
convs = {5: convert_perc, 12: convert_perc, 13: convert_perc, 15: convert_perc, 16: convert_perc, 20: convert_perc}

url = 'http://fundamentus.com.br/resultado.php'
agent = {"User-Agent":"Mozzila/5.0"}
resposta = requests.get(url, headers = agent)
soup = BeautifulSoup(resposta.text, 'lxml')
tabela = soup.find_all('table')[0]
df = pd.read_html(str(tabela), decimal = ',', thousands='.', converters=convs)[0]
fundamentus = df

#Data cleaning
fundamentus = fundamentus[fundamentus.isnull().any(axis=1)]

for column in ['P/L', 'P/VP','PSR',  'EV/EBITDA']:
    fundamentus[column].fillna(fundamentus[column].mean(), inplace = True)

fundamentus = fundamentus.drop( ['Div.Yield', 'P/Ativo','P/Cap.Giro', 'P/EBIT', 'P/Ativ Circ.Liq', 'EV/EBIT',
                                'Mrg Ebit', 'Mrg. Líq.', 'Liq. Corr.', 'ROIC', 'ROE', 
                                'Liq.2meses','Patrim. Líq', 'Dív.Brut/ Patrim.', 'Cresc. Rec.5a'], axis=1)


## Calculando percentual dos indicadore
metrics = {
            'P/L': 'P/L Percentile',
            'P/VP':'P/VP Percentile',
            'PSR': 'PSR Percentile',
            'EV/EBITDA':'EV/EBITDA Percentile'
}

for row in fundamentus.index:
    for metric in metrics.keys():
        fundamentus.loc[row, metrics[metric]] = stats.percentileofscore(fundamentus[metric], fundamentus.loc[row, metric])/100


# STREAMLIT 

st.title("Estratégia Quantamental")

ticker = fundamentus['Papel']+'.SA'
ticker = ticker.tolist()
ticker = st.selectbox('Escolha um ativo', ticker)
