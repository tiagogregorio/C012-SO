"""Diagrama de Gantt idêntico ao material do professor
  • FCFS, SJF e Round Robin com cálculo correto
  • Race Condition nos preços das ações 

Uso: python main.py
"""
import tkinter as tk
import threading

from loops import loop_gerador, loop_escalonador, loop_ruido, loop_candles
from ui import HomeBroker

def main():
    for fn in [loop_gerador, loop_escalonador, loop_ruido, loop_candles]:
        threading.Thread(target=fn, daemon=True).start()
    root = tk.Tk()
    HomeBroker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
