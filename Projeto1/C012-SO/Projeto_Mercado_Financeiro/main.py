"""
PONTO DE ENTRADA (main.py)
Responsável por orquestrar a inicialização do sistema.
"""

import tkinter as tk
from models import EstadoMercado
from engine import iniciar_engine
from interface import HomeBroker

def main():
    # 1. Instancia a "Data Section" compartilhada
    # Este objeto será passado para a Engine (escrever) e para a GUI (ler)
    mercado = EstadoMercado()

    # 2. Inicia os serviços de background (Threads de Kernel)
    # Passamos o objeto 'mercado' para que as threads saibam onde alterar os preços
    iniciar_engine(mercado)

    # 3. Inicializa a Interface Gráfica (Main Thread)
    # O Tkinter DEVE rodar na thread principal para evitar crashes de vídeo
    root = tk.Tk()
    
    # Criamos a aplicação passando o estado do mercado
    app = HomeBroker(root, mercado)

    # 4. Loop principal da interface
    # Daqui para frente, o controle é do gerenciador de eventos do Tkinter
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[SISTEMA] Encerrando simulação com segurança...")

if __name__ == "__main__":
    main()