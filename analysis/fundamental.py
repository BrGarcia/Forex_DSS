import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import pandas as pd

class FundamentalAnalyzer:
    def __init__(self, moedas=["EUR", "USD"]):
        self.moedas = moedas
        # Feed XML oficial e gratuito da Forex Factory (Atualizado semanalmente)
        self.url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

    def buscar_noticias_hoje(self):
        """Busca notícias de Alto Impacto para as moedas do par no dia atual"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []

            root = ET.fromstring(response.content)
            noticias_perigosas = []
            hoje = datetime.now().strftime("%m-%d-%Y") # Formato do XML da FF

            for evento in root.findall('event'):
                data_evento = evento.find('date').text
                moeda = evento.find('country').text
                impacto = evento.find('impact').text
                titulo = evento.find('title').text
                hora = evento.find('time').text

                # Filtra: Apenas hoje, apenas moedas do bot, apenas ALTO impacto (High)
                if data_evento == hoje and moeda in self.moedas and impacto == "High":
                    noticias_perigosas.append({
                        "hora": hora,
                        "moeda": moeda,
                        "titulo": titulo
                    })

            return noticias_perigosas

        except Exception as e:
            print(f"⚠️ Erro ao buscar calendário econômico: {e}")
            return []

    def gerar_alerta_radar(self):
        """Gera uma string formatada para o Radar se houver perigo"""
        noticias = self.buscar_noticias_hoje()
        
        if not noticias:
            return "✅ Sem notícias de Alto Impacto (Caminho Livre)"
        
        alertas = []
        for n in noticias:
            alertas.append(f"🔴 {n['hora']} - {n['moeda']}: {n['titulo']}")
            
        return "\n".join(alertas)
