#!/bin/bash

echo "🚀 Preparando os motores do Forex Advisor..."

# 1. Verifica se a pasta .venv (padrão do VS Code) existe. Se não, cria.
if [ ! -d ".venv" ]; then
    echo "⚠️ Ambiente virtual não encontrado. Criando .venv..."
    python -m venv .venv
fi

# 2. Ativa o ambiente
source .venv/bin/activate

# 3. Verifica as bibliotecas (o --quiet faz com que ele instale rápido e sem poluir a tela, 
# a menos que falte alguma coisa)
echo "📦 Checando as bibliotecas matemáticas..."
pip install -r requirements.txt --quiet

# 4. Inicia o Bot
echo "🟢 Sistema pronto! Ligando o Radar..."
python main.py

# 5. Desliga a proteção ao sair
deactivate