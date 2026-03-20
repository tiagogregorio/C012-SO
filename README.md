Simulação Caótica do Mercado Financeiro — Threads
Trabalho Prático — Sistemas Operacionais

 Sobre o Projeto
Simulador caótico do mercado financeiro brasileiro (BOVESPA) desenvolvido em Python, com o objetivo de demonstrar na prática os conceitos do Capítulo 04 — Threads da disciplina de Sistemas Operacionais.
O simulador dispara múltiplas Threads, cada uma representando uma notícia de mercado que impacta os preços de 10 ações reais do Ibovespa. À medida que o número de threads aumenta, 
o sistema demonstra os efeitos de concorrência, contenção de mutex, colisão na seção crítica e, nos níveis mais altos, o travamento real do processo.

Faixas do Slider de Threads:
Mercado normal 🟢 Verde (1-4)
Mercado agitado - caos crescente🟢 Verde claro (5-9)
Mercado em pânico 🟡 Amarelo (10-15)
SATURAÇÃO — perigo de travamento real🔴 Vermelho (16-22)

Requisitos
Python 3.8 ou superior
Tkinter (já incluído na instalação padrão do Python)
Sistema Operacional: Windows, Linux ou macOS

Referências
Silberschatz, A.; Galvin, P. B.; Gagne, G. Operating System Concepts, 9ª ed.
Slides do Professor — Capítulo 04: Threads — INATEL
Documentação oficial do módulo threading — Python
Tkinter — Python GUI
