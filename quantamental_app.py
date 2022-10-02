import pandas as pd
import requests
import math
from bs4 import BeautifulSoup
from scipy import stats 
import yfinance as yf
import streamlit as st
import datetime
from statistics import mean

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
#fundamentus = fundamentus[fundamentus.isnull().any(axis=1)]

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

# Limpando valores com a cotação = 0
fundamentus = fundamentus.loc[fundamentus['Cotação'] != 0.00]

# RV Score

for row in fundamentus.index:
    value_percentiles = []
    for metric in metrics.keys():
        value_percentiles.append(fundamentus.loc[row, metrics[metric]])
    fundamentus.loc[row, 'RV Score'] = mean(value_percentiles)

#Selecionando as 50 melhores ações

fundamentus = fundamentus[:50]
fundamentus.reset_index(drop = True, inplace = True)


### STREAMLIT  ###

st.title("Estratégia Quantamental")

st.markdown('Value invest é uma estratégia que consiste em comprar ações que estão abaixo do valor de mercado da empresa. A ideia resumidamente é comprar ações de companhias que estejam subvalorizadas no mercado')
st.markdown('Para fazer isso foram selecionadas empresas com bons indicativos financeiros. Porém cada indicador financeiro tem algumas falhas')
st.markdown('Por exemplo, a relação preço/lucro não funciona bem com ações com lucros negativos.')
st.markdown('Da mesma forma, as ações que recompram suas próprias ações são difíceis de avaliar usando a relação price-to-book ratio (P/VBA ou P/B).')
st.markdown('Os investidores normalmente usam uma cesta composta de métricas de avaliação para construir estratégias de valor quantitativas robustas. Nesta estratégia, foram filtradas as ações com os percentis mais baixos nas seguintes métricas:')
st.markdown('     - P/L')
st.markdown('     - P/VBA ou P/B')
st.markdown('     - PSR')
st.markdown('     - EV/EBITDA')
st.markdown('Para montar uma carteira, selecione o valor de investimento que deseja para esta carteira e o modelo apresenta as ações a quantidade de ações de cada empresa que vc deve comprar para alocar seu capital igualmente em cada ativo.')


#Numero de ações p/comrprar


portfolio_size = st.number_input('Qual valor da sua carteira(R$)',min_value = 1000000)

position_size = float(portfolio_size) / len(fundamentus.index)
try: 
    for i in range(0, len(fundamentus['Papel'])-1):
        fundamentus.loc[i, 'Numero de ações p/ comprar'] = math.floor(position_size / fundamentus['Cotação'][i])
except:pass


nova_lista = fundamentus[['Papel','Cotação','P/L', 'P/VP','PSR', 'EV/EBITDA','Numero de ações p/ comprar' ]]
st.dataframe(nova_lista)

