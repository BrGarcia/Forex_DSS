from analysis.fundamental import FundamentalAnalyzer

def testar_escudo():
    print("🔍 Iniciando teste do Analista Fundamentalista...")
    
    # Instancia o analisador para EUR e USD
    analyzer = FundamentalAnalyzer(moedas=["EUR", "USD"])
    
    print("📡 Conectando à Forex Factory...")
    alertas = analyzer.gerar_alerta_radar()
    
    print("\n" + "="*50)
    print("🛡️ RESULTADO DO ESCUDO")
    print("="*50)
    print(alertas)
    print("="*50)

if __name__ == "__main__":
    testar_escudo()
