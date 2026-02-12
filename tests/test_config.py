import sys
import os

from pathlib import Path

# --- CORREÇÃO DE IMPORTAÇÃO ---
# Pega o caminho deste arquivo (tests/test_config.py)
current_file = Path(__file__).resolve()

# Pega o diretório "pai do pai" (A raiz do projeto: ForexSystem_Project)
project_root = current_file.parent.parent

# Adiciona a raiz ao sistema de busca do Python
sys.path.append(str(project_root))

# ------------------------------

try:
    # Agora o Python consegue encontrar 'shared'
    from shared.config import Config
    print("✅ SUCESSO: Importação do módulo 'shared' funcionou!")
except ImportError as e:
    print(f"❌ ERRO CRÍTICO: O Python não encontrou a pasta 'shared'.")
    print(f"   Caminho tentado: {project_root}")
    print(f"   Detalhe do erro: {e}")
    sys.exit(1)

def run_test():
    print(f"\n--- TESTANDO CONFIGURAÇÃO (De dentro de /tests) ---")
    print(f"📂 Raiz do Projeto detectada: {Config.BASE_DIR}")
    
    # Teste rápido de acesso
    if Config.MT5_LOGIN:
        print(f"✅ Variáveis de ambiente (.env) lidas corretamente.")
    else:
        print(f"⚠️  Aviso: Login MT5 não encontrado ou é 0.")

    print("\nTeste concluído.")

if __name__ == "__main__":
    run_test()