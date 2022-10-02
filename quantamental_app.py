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

#Numero de ações p/comrprar


portfolio_size = st.number_input('Qual valor da sua carteira(R$)',min_value = 1000000)

st.text(portfolio_size)

position_size = float(portfolio_size) / len(fundamentus.index)
try: 
    for i in range(0, len(fundamentus['Papel'])-1):
        fundamentus.loc[i, 'Numero de ações p/ comprar'] = math.floor(position_size / fundamentus['Cotação'][i])
except:pass


nova_lista = fundamentus[['Papel','Cotação','P/L', 'P/VP','PSR', 'EV/EBITDA','Numero de ações p/ comprar' ]]
st.dataframe(nova_lista)


#Varifando informações obre ativos especificos da carteira
st.text('Veja informações sobre um ativo específico desta carteira')
ticker = fundamentus['Papel']+'.SA'
ticker = ticker.tolist()
ticker = st.selectbox('Escolha um ativo', ticker)

### STOCK INFORMATIONN ####

st.write('---')
col1,col2 = st.columns(2)
with col1:
    # Sidebar
    st.subheader('Query parameters')
    start_date = st.date_input("Start date", datetime.date(2022, 1, 1))
    end_date = st.date_input("End date", datetime.date(2022, 1, 31))

with col2: 
    # Retrieving tickers data
   #tickerSymbol = st.selectbox('Stock ticker', top50_ibov) # Select ticker symbol
    tickerData = yf.Ticker(ticker) # Get ticker data
    tickerDf = tickerData.history(period='1d', start=start_date, end=end_date) #get the historical prices for this ticker
    # Ticker data
    st.header('**Ticker data**')
    st.write(tickerDf)

# Ticker information
string_logo = '<img src=%s>' % tickerData.info['logo_url']
st.markdown(string_logo, unsafe_allow_html=True)

string_name = tickerData.info['longName']
st.header('**%s**' % string_name)

string_summary = tickerData.info['longBusinessSummary']
st.info(string_summary)
