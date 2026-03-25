#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# --- CONFIGURAÇÃO: Defina aqui quais extensões de arquivo devem ter seu conteúdo lido ---
# Note que .json NÃO está na lista, então será ignorado.
EXTENSOES_PERMITIDAS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', 
    '.java', '.c', '.cpp', '.h', '.cs', 
    '.go', '.rs', '.php', '.rb', '.sh', 
    '.sql', '.html', '.css', '.vue', '.dart'
}

# Arquivos sem extensão que geralmente são código/configuração úteis
ARQUIVOS_ESPECIFICOS = {'Dockerfile', 'Makefile', 'Jenkinsfile'}

def arquivo_eh_codigo(nome_arquivo):
    """Verifica se o arquivo é de programação baseado na extensão."""
    _, extensao = os.path.splitext(nome_arquivo)
    # Verifica se a extensão está na lista permitida OU se é um arquivo específico (ex: Dockerfile)
    return (extensao.lower() in EXTENSOES_PERMITIDAS) or (nome_arquivo in ARQUIVOS_ESPECIFICOS)

def gerar_arvore_e_coletar_arquivos(diretorio_raiz, lista_de_arquivos, prefixo='', arquivo_saida=sys.stdout):
    try:
        itens = sorted(os.listdir(diretorio_raiz))
        total_itens = len(itens)
    except (PermissionError, FileNotFoundError):
        return

    for i, nome_item in enumerate(itens):
        caminho_completo = os.path.join(diretorio_raiz, nome_item)
        eh_ultimo = (i == total_itens - 1)

        conector = '└── ' if eh_ultimo else '├── '
        
        # Imprime a árvore visualmente (mostra todos os arquivos para contexto da estrutura)
        print(f"{prefixo}{conector}{nome_item}", file=arquivo_saida)

        if os.path.isdir(caminho_completo):
            # Ignora pastas comuns que não queremos ler (opcional, ex: node_modules, .git)
            if nome_item in ['.git', '__pycache__', 'node_modules', 'venv', '.idea', '.vscode']:
                continue

            prefixo_para_dentro = prefixo + ('    ' if eh_ultimo else '│   ')
            gerar_arvore_e_coletar_arquivos(caminho_completo, lista_de_arquivos, prefixo_para_dentro, arquivo_saida)
            
        elif os.path.isfile(caminho_completo):
            # AQUI ESTÁ A MUDANÇA PRINCIPAL:
            # Só adiciona na lista para leitura se passar no filtro
            if arquivo_eh_codigo(nome_item):
                lista_de_arquivos.append(caminho_completo)

def imprimir_conteudo_dos_arquivos(lista_de_arquivos, pasta_base, arquivo_saida=sys.stdout):
    print("\n" + "="*25 + " CONTEÚDO DOS ARQUIVOS " + "="*25, file=arquivo_saida)
    
    if not lista_de_arquivos:
        print("\nNenhum arquivo de código encontrado nas extensões configuradas.", file=arquivo_saida)
        return

    for caminho_arquivo in lista_de_arquivos:
        caminho_relativo = os.path.relpath(caminho_arquivo, pasta_base)
        print(f"\n\n---[ {caminho_relativo} ]---", file=arquivo_saida)
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
            print(conteudo, file=arquivo_saida)
        except Exception as e:
            print(f"(Não foi possível ler o conteúdo: {e})", file=arquivo_saida)
    
    print("\n" + "="*70, file=arquivo_saida)


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 main.py <caminho_da_pasta>")
        sys.exit(1)

    pasta_alvo = sys.argv[1]

    if not os.path.isdir(pasta_alvo):
        print(f"Erro: O caminho '{pasta_alvo}' não é um diretório válido.")
        sys.exit(1)

    nome_do_arquivo_txt = "relatorio_projeto.txt"

    print(f"Lendo diretório: {pasta_alvo}...")
    print(f"Filtrando apenas arquivos de programação...")
    print(f"Escrevendo resultados em: {nome_do_arquivo_txt}")

    with open(nome_do_arquivo_txt, 'w', encoding='utf-8') as f_out:
        
        print(f"Estrutura da pasta: {pasta_alvo}", file=f_out)
        
        arquivos_encontrados = []
        
        # PARTE 1: Gera a árvore e seleciona arquivos
        gerar_arvore_e_coletar_arquivos(pasta_alvo, arquivos_encontrados, arquivo_saida=f_out)

        # PARTE 2: Imprime conteúdo apenas dos selecionados
        imprimir_conteudo_dos_arquivos(arquivos_encontrados, pasta_alvo, arquivo_saida=f_out)

    print("Sucesso! O arquivo foi gerado.")

if __name__ == "__main__":
    main()
