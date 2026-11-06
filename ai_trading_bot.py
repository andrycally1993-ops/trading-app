import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import ccxt
import time

# 1. Configurazione della connessione a OKX con le tue chiavi e modalità Sandbox attiva
exchange = ccxt.okx({
    'apiKey': 'c2471984-de24-43a6-80e7-5659d2ade688',
    'secret': 'AE7AC7EF876B20737FD5536D7BABA004',
    'password': 'King_9396',
    'enableRateLimit': True,
})

exchange.set_sandbox_mode(True)

def calcola_rsi(serie, periodo=14):
    delta = serie.diff()
    guadagno = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdita = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = guadagno / perdita
    return 100 - (100 / (1 + rs))

def esegui_trading_automatico():
    symbol = 'BTC/USDT'
    print(f"\n--- Avvio analisi avanzata con IA e Multi-Indicatori per {symbol} ---")
    
    # Prezzo corrente in tempo reale
    ticker = exchange.fetch_ticker(symbol)
    prezzo_attuale = ticker['last']
    print(f"Prezzo attuale di {symbol}: ${prezzo_attuale:,.2f}")
    
    # Recupero dati storici estesi per calcolare gli indicatori
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=200)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # --- CALCOLO DEGLI INDICATORI TECNICI ---
    df['rsi'] = calcola_rsi(df['close'], periodo=14)
    df['sma_10'] = df['close'].rolling(window=10).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
    
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    sma_20 = df['close'].rolling(window=20).mean()
    std_20 = df['close'].rolling(window=20).std()
    df['bollinger_upper'] = sma_20 + (std_20 * 2)
    df['bollinger_lower'] = sma_20 - (std_20 * 2)
    df['bollinger_width'] = (df['bollinger_upper'] - df['bollinger_lower']) / sma_20
    
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()
    
    df.dropna(inplace=True)
    
    feature_columns = ['rsi', 'sma_10', 'sma_50', 'macd', 'macd_signal', 'bollinger_width', 'atr', 'volume']
    df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)
    df.dropna(inplace=True)
    
    X = df[feature_columns].values
    y = df['target'].values
    
    # Addestramento del modello Random Forest avanzato
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X[:-1], y[:-1])
    
    ultimi_dati = X[-1].reshape(1, -1)
    previsione = model.predict(ultimi_dati)[0]
    
    print("Analisi multi-indicatore dell'IA completata.")
    
    quantita_ordine = 0.001
    if previsione == 1:
        print("L'IA rileva un segnale di RIALZO (BUY) basato su tutti gli indicatori.")
        print(f"Simulazione ordine di ACQUISTO di {quantita_ordine} BTC a ${prezzo_attuale:,.2f} in corso...")
        # exchange.create_market_buy_order(symbol, quantita_ordine)
        print(">>> Ordine di ACQUISTO simulato con successo!")
    else:
        print("L'IA rileva un segnale di RIBASSO (SELL) basato su tutti gli indicatori.")
        print(f"Simulazione ordine di VENDITA di {quantita_ordine} BTC a ${prezzo_attuale:,.2f} in corso...")
        # exchange.create_market_sell_order(symbol, quantita_ordine)
        print(">>> Ordine di VENDITA simulato con successo!")

if __name__ == "__main__":
    print("=== AVVIO BOT DI TRADING AUTONOMO CON IA ===")
    print("Il bot eseguirà un'analisi automatica ogni 1 ora.")
    print("Premi Ctrl + C nel terminale in qualsiasi momento per fermarlo.\n")
    
    while True:
        try:
            esegui_trading_automatico()
        except Exception as e:
            print(f"⚠️ Si è verificato un errore temporaneo: {e}")
        
        print("\n⏳ In attesa del prossimo ciclo (tra 1 ora)...\n")
        time.sleep(10)  # Pausa di 3600 secondi (1 ora)