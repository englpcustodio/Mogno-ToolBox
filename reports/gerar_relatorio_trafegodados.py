import os
import numpy as np
from datetime import datetime
import pandas as pd
import re
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as ExcelImage
from utils.helpers import auto_size_columns
from utils.logger import adicionar_log

DIR_DATA_TRAFFIC = 'relatorios_gerados/trafego_dados_servidor'

def limpar_dados(dados):
    """Remove caracteres inválidos da string e retorna o valor limpo."""
    return ''.join(c for c in dados if c.isprintable() and c not in ('\r', '\n', '\t')).strip()

def relatorio_trafegodados_excel(trafego_dados):
    if not os.path.exists(DIR_DATA_TRAFFIC):
        os.makedirs(DIR_DATA_TRAFFIC)

    data_hora_formatada = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f'relatorio_trafegodados_{data_hora_formatada}.xlsx'
    caminho_arquivo = os.path.join(DIR_DATA_TRAFFIC, nome_arquivo)

    dados = {
        "Serial": [],
        "Tráfego de dados [bytes]": [],
        "Tráfego de dados [kB]": [],
        "Tráfego de dados [MB]": [],
        "Tráfego de dados [GB]": []
    }

    for serial, valor in trafego_dados.items():
        try:
            serial_decodificado = limpar_dados(str(serial))
            if not re.match(r'^[a-zA-Z0-9]+$', serial_decodificado):
                print(f"Serial inválido descartado: {serial_decodificado}")
                continue
        except Exception as e:
            print(f"Erro ao processar serial: {serial} -> {e}")
            continue

        valor_limpo = limpar_dados(str(valor))
        try:
            valor_convertido = int(valor_limpo)
        except ValueError:
            print(f"Valor inválido descartado para serial {serial_decodificado}: {valor_limpo}")
            continue

        dados["Serial"].append(serial_decodificado)
        dados["Tráfego de dados [bytes]"].append(valor_convertido)
        dados["Tráfego de dados [kB]"].append(valor_convertido / 1024)
        dados["Tráfego de dados [MB]"].append(valor_convertido / (1024 ** 2))
        dados["Tráfego de dados [GB]"].append(valor_convertido / (1024 ** 3))

        

    if dados["Serial"]:
        df = pd.DataFrame(dados)
        df = df.sort_values(by="Tráfego de dados [bytes]", ascending=False)

        # Total de seriais consultados
        total_seriais = len(dados["Serial"])

        # Consumo máximo
        consumo_maximo = df.loc[df["Tráfego de dados [bytes]"].idxmax()]
        serial_maximo = consumo_maximo["Serial"]
        valor_maximo_mb = consumo_maximo["Tráfego de dados [MB]"]

        # Consumo médio
        consumo_medio = df["Tráfego de dados [MB]"].mean()

        try:
            # Salvar os dados brutos na aba 'seriais_consumo'
            with pd.ExcelWriter(caminho_arquivo) as writer:
                df.to_excel(writer, sheet_name='seriais_consumo', index=False)
        
                # Ajustar o tamanho das colunas da aba 'seriais_consumo'
                auto_size_columns(writer.sheets['seriais_consumo'])
                
                # Criar a aba 'dados_grafico'
                info_sheet = writer.book.create_sheet(title="dados_grafico")

                # Antes de calcular as faixas

                # Antes de calcular as faixas
                plt.figure(figsize=(10, 6))
                
                # Ajustar a configuração dos bins
                bins = [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]  # Bins sem zero
                
                # Criar histograma
                hist, edges = np.histogram(df["Tráfego de dados [MB]"], bins=bins)
                
                # Calcular porcentagens
                porcentagens = (hist / hist.sum()) * 100
                
                # Verificar se existem dados suficientes para plotar
                if hist.sum() == 0:
                    print("Aviso: Nenhum dado para plotar. O gráfico será branco.")
                else:
                    # Adicionar as informações na aba 'dados_grafico'
                    info_sheet.append(["Total de Seriais Consultados", total_seriais])
                    info_sheet.append(["Consumo Máximo - Serial", "Valor (MB)"])
                    info_sheet.append([serial_maximo, f"{valor_maximo_mb:.2f} MB"])
                    info_sheet.append(["Consumo Médio (MB)", f"{consumo_medio:.2f} MB"])
                    info_sheet.append([])  # Linha em branco para separação
                
                    # Adicionar cabeçalho para as faixas de consumo
                    info_sheet.append(["Faixa de MB", "Quantidade de Equipamentos", "Porcentagem"])
                
                    # Calcular a quantidade de equipamentos em cada faixa e suas porcentagens
                    faixas = bins[:-1]  # Limites inferiores de cada faixa
                    quantidade_equipamentos = hist  # Contagem de equipamentos em cada faixa
                
                    for i in range(len(faixas)):
                        faixa_label = f"{faixas[i]} a {bins[i + 1]}"
                        porcentagem = f"{porcentagens[i]:.2f}%"
                        info_sheet.append([faixa_label, quantidade_equipamentos[i], porcentagem])
                
                    # Gerar o gráfico
                    plt.bar(edges[:-1], porcentagens, width=np.diff(edges), edgecolor='black', align='edge')
                
                    # Otimização dos eixos
                    plt.xscale('log')  # Definindo o eixo X como logarítmico
                    plt.title("Distribuição de Tráfego de Dados por Faixas (MB) [Escala Logarítmica]")
                    plt.xlabel("Faixa de Consumo (MB)")
                    plt.ylabel("Porcentagem de Equipamentos (%)")
                
                    # Ajustar limites do eixo Y com base nos dados
                    plt.ylim(0, min(100, max(porcentagens) * 1.1))  # Evita que o gráfico extrapole 100%
                
                    # Ajuste automático para o eixo X, evitando zero
                    plt.xlim(left=0.1, right=max(bins))  # Começando de um valor positivo
                
                    plt.xticks(bins)  # Novos limites de bins
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                    # Salvar gráfico como imagem temporária
                    imagem_grafico = os.path.join(DIR_DATA_TRAFFIC, f"grafico_trafego_{data_hora_formatada}.png")
                    plt.tight_layout()
                    plt.savefig(imagem_grafico)
                    plt.close()
                
                    # Adicionar o gráfico à aba 'dados_grafico' na coluna D
                    img = ExcelImage(imagem_grafico)
                    img.anchor = 'D1'
                    info_sheet.add_image(img)
                

                # Salvar gráfico como imagem temporária
                imagem_grafico = os.path.join(DIR_DATA_TRAFFIC, f"grafico_trafego_{data_hora_formatada}.png")
                plt.tight_layout()
                plt.savefig(imagem_grafico)
                plt.close()

                # Adicionar o gráfico à aba 'dados_grafico' na coluna D
                img = ExcelImage(imagem_grafico)
                img.anchor = 'D1'
                info_sheet.add_image(img)

                # Ajustar o tamanho das colunas da aba 'dados_grafico'

                auto_size_columns(info_sheet)

            adicionar_log(f"📁 Relatório gerado: {caminho_arquivo}")
            return caminho_arquivo
        
        except Exception as e:
            print(f"Erro ao salvar o arquivo Excel: {e}.")
            print("Possíveis problemas com os dados:")
            print(df)
    else:
        print("Nenhum dado válido foi encontrado para salvar.")

    print(f"Dados processados: {len(dados['Serial'])} seriais válidos.")

# Exemplo de uso (substitua pelo seu conjunto de dados)
# trafego_dados = { ... }  # dicionário com seus dados
# relatorio_trafegodados_excel(trafego_dados)
