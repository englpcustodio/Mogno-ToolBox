"""
Gerador de Gráficos para Relatórios de Última Posição
Lê dados do Excel e gera visualizações para análise de frota.

Autor: Inner AI
Data: 2025-01-30
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import numpy as np
from pathlib import Path

# Configuração de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class GeradorGraficosRelatorio:
    """
    Classe para gerar gráficos de análise de relatórios de última posição.
    """

    def __init__(self, arquivo_excel, aba_modelo_hw="Planilha1"):
        """
        Inicializa o gerador de gráficos.

        Args:
            arquivo_excel: Caminho para o arquivo Excel
            aba_modelo_hw: Nome da aba com dados de Modelo de HW
        """
        self.arquivo = arquivo_excel
        self.aba_modelo = aba_modelo_hw
        self.df_modelo = None
        self.output_dir = "graficos_relatorio"

        # Cria diretório de saída
        Path(self.output_dir).mkdir(exist_ok=True)

        # Carrega dados
        self._carregar_dados()

    def _carregar_dados(self):
        """Carrega dados do Excel."""
        try:
            self.df_modelo = pd.read_excel(self.arquivo, sheet_name=self.aba_modelo)

            # Remove linhas com NaN no modelo
            self.df_modelo = self.df_modelo[self.df_modelo['Modelo de HW'] != 'NaN']

            # Converte percentuais para float
            for col in self.df_modelo.columns:
                if '[%]' in col:
                    self.df_modelo[col] = self.df_modelo[col].str.rstrip('%').astype('float')

            print(f"✅ Dados carregados: {len(self.df_modelo)} modelos")

        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            raise

    # =========================================================================
    # 1. PARETO POR MODELO (Quantidade Encontrada)
    # =========================================================================

    def grafico_1_pareto_modelos(self):
        """Gráfico de Pareto mostrando concentração de modelos."""
        fig, ax1 = plt.subplots(figsize=(14, 7))

        # Ordena por quantidade
        df_sorted = self.df_modelo.sort_values('Quantidade encontrada', ascending=False)

        # Calcula percentual acumulado
        total = df_sorted['Quantidade encontrada'].sum()
        df_sorted['Percentual'] = (df_sorted['Quantidade encontrada'] / total * 100)
        df_sorted['Acumulado'] = df_sorted['Percentual'].cumsum()

        # Barras
        x = range(len(df_sorted))
        ax1.bar(x, df_sorted['Quantidade encontrada'], color='steelblue', alpha=0.8)
        ax1.set_xlabel('Modelo de HW', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Quantidade Encontrada', fontsize=12, fontweight='bold', color='steelblue')
        ax1.tick_params(axis='y', labelcolor='steelblue')
        ax1.set_xticks(x)
        ax1.set_xticklabels(df_sorted['Modelo de HW'], rotation=45, ha='right')

        # Linha acumulada
        ax2 = ax1.twinx()
        ax2.plot(x, df_sorted['Acumulado'], color='red', marker='o', linewidth=2, markersize=6)
        ax2.set_ylabel('Percentual Acumulado (%)', fontsize=12, fontweight='bold', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.set_ylim(0, 105)
        ax2.axhline(80, color='orange', linestyle='--', alpha=0.5, label='80% da frota')

        plt.title('Pareto: Concentração de Modelos na Frota', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '01_pareto_modelos.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 1 salvo: {caminho}")

    # =========================================================================
    # 2. HEATMAP DE RECÊNCIA GSM POR MODELO
    # =========================================================================

    def grafico_2_heatmap_recencia(self):
        """Heatmap mostrando saúde de comunicação GSM por modelo."""
        fig, ax = plt.subplots(figsize=(12, 10))

        # Seleciona colunas de períodos GSM
        cols_periodos = [
            'Posição GSM Hoje',
            'Posição GSM 1-7',
            'Posição GSM 8-15',
            'Posição GSM +16'
        ]

        # Cria matriz de dados
        df_heat = self.df_modelo.set_index('Modelo de HW')[cols_periodos]

        # Heatmap
        sns.heatmap(df_heat, annot=True, fmt='g', cmap='RdYlGn_r', 
                    linewidths=0.5, cbar_kws={'label': 'Quantidade de Equipamentos'},
                    ax=ax)

        plt.title('Heatmap: Recência de Comunicação GSM por Modelo', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Período desde última posição', fontsize=12, fontweight='bold')
        plt.ylabel('Modelo de HW', fontsize=12, fontweight='bold')
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '02_heatmap_recencia_gsm.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 2 salvo: {caminho}")

    # =========================================================================
    # 3. BARRAS EMPILHADAS - DISTRIBUIÇÃO GSM POR PERÍODO
    # =========================================================================

    def grafico_3_barras_empilhadas_gsm(self):
        """Barras empilhadas mostrando distribuição de períodos GSM."""
        fig, ax = plt.subplots(figsize=(12, 10))

        # Seleciona top 10 modelos
        top_modelos = self.df_modelo.nlargest(10, 'Quantidade encontrada')

        # Dados
        modelos = top_modelos['Modelo de HW']
        hoje = top_modelos['Posição GSM Hoje']
        dias_1_7 = top_modelos['Posição GSM 1-7']
        dias_8_15 = top_modelos['Posição GSM 8-15']
        dias_16_mais = top_modelos['Posição GSM +16']

        # Barras empilhadas horizontais
        y_pos = np.arange(len(modelos))

        ax.barh(y_pos, hoje, label='Hoje', color='#2ecc71')
        ax.barh(y_pos, dias_1_7, left=hoje, label='1-7 dias', color='#f39c12')
        ax.barh(y_pos, dias_8_15, left=hoje+dias_1_7, label='8-15 dias', color='#e67e22')
        ax.barh(y_pos, dias_16_mais, left=hoje+dias_1_7+dias_8_15, label='+16 dias', color='#e74c3c')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(modelos)
        ax.set_xlabel('Quantidade de Equipamentos', fontsize=12, fontweight='bold')
        ax.set_ylabel('Modelo de HW', fontsize=12, fontweight='bold')
        ax.legend(loc='lower right', fontsize=10)

        plt.title('Distribuição de Recência GSM por Modelo (Top 10)', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '03_barras_empilhadas_gsm.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 3 salvo: {caminho}")

    # =========================================================================
    # 4. RADAR CHART - PERFIL DE SAÚDE GSM
    # =========================================================================

    def grafico_4_radar_saude_gsm(self):
        """Radar chart comparando perfil de saúde de 3 modelos."""
        # Seleciona 3 modelos: melhor, pior, intermediário
        df_sorted = self.df_modelo.sort_values('Posição GSM Hoje [%]', ascending=False)

        melhor = df_sorted.iloc[0]
        pior = df_sorted.iloc[-1]
        intermediario = df_sorted.iloc[len(df_sorted)//2]

        # Categorias
        categorias = ['Hoje [%]', '1-7 dias [%]', '8-15 dias [%]', '+16 dias [%]']

        # Dados
        melhor_vals = [
            melhor['Posição GSM Hoje [%]'],
            melhor['Posição GSM 1-7 [%]'],
            melhor['Posição GSM 8-15 [%]'],
            melhor['Posição GSM +16 [%]']
        ]

        pior_vals = [
            pior['Posição GSM Hoje [%]'],
            pior['Posição GSM 1-7 [%]'],
            pior['Posição GSM 8-15 [%]'],
            pior['Posição GSM +16 [%]']
        ]

        inter_vals = [
            intermediario['Posição GSM Hoje [%]'],
            intermediario['Posição GSM 1-7 [%]'],
            intermediario['Posição GSM 8-15 [%]'],
            intermediario['Posição GSM +16 [%]']
        ]

        # Fecha o polígono
        melhor_vals += melhor_vals[:1]
        pior_vals += pior_vals[:1]
        inter_vals += inter_vals[:1]

        # Ângulos
        angles = np.linspace(0, 2 * np.pi, len(categorias), endpoint=False).tolist()
        angles += angles[:1]

        # Plot
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        ax.plot(angles, melhor_vals, 'o-', linewidth=2, label=f"Melhor: {melhor['Modelo de HW']}", color='green')
        ax.fill(angles, melhor_vals, alpha=0.25, color='green')

        ax.plot(angles, inter_vals, 'o-', linewidth=2, label=f"Intermediário: {intermediario['Modelo de HW']}", color='orange')
        ax.fill(angles, inter_vals, alpha=0.25, color='orange')

        ax.plot(angles, pior_vals, 'o-', linewidth=2, label=f"Pior: {pior['Modelo de HW']}", color='red')
        ax.fill(angles, pior_vals, alpha=0.25, color='red')

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categorias, fontsize=11)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        ax.grid(True)

        plt.title('Radar: Perfil de Saúde GSM por Modelo', 
                  fontsize=16, fontweight='bold', pad=30)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '04_radar_saude_gsm.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 4 salvo: {caminho}")

    # =========================================================================
    # 5. ROSCA - DISTRIBUIÇÃO DE MODELOS
    # =========================================================================

    def grafico_5_rosca_distribuicao_modelos(self):
        """Gráfico de rosca mostrando proporção da frota por modelo."""
        fig, ax = plt.subplots(figsize=(12, 8))

        # Top 8 modelos + outros
        top_n = 8
        df_sorted = self.df_modelo.sort_values('Quantidade encontrada', ascending=False)

        top_modelos = df_sorted.head(top_n)
        outros = df_sorted.iloc[top_n:]['Quantidade encontrada'].sum()

        labels = list(top_modelos['Modelo de HW']) + ['Outros']
        sizes = list(top_modelos['Quantidade encontrada']) + [outros]

        # Cores
        colors = plt.cm.Set3(range(len(labels)))

        # Rosca
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                            startangle=90, colors=colors,
                                            wedgeprops=dict(width=0.4, edgecolor='white'))

        # Estilo dos textos
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        plt.title('Distribuição da Frota por Modelo de HW', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '05_rosca_distribuicao_modelos.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 5 salvo: {caminho}")

    # =========================================================================
    # 6. ROSCA - SAUDÁVEL VS NÃO SAUDÁVEL
    # =========================================================================

    def grafico_6_rosca_saude_geral(self):
        """Gráfico de rosca mostrando saúde geral da frota."""
        fig, ax = plt.subplots(figsize=(10, 8))

        # Soma total por período
        saudavel = self.df_modelo['Posição GSM Hoje'].sum()
        degradado = self.df_modelo['Posição GSM 1-7'].sum()
        critico = self.df_modelo['Posição GSM 8-15'].sum()
        morto = self.df_modelo['Posição GSM +16'].sum()

        labels = ['Saudável (Hoje)', 'Degradado (1-7 dias)', 'Crítico (8-15 dias)', 'Morto (+16 dias)']
        sizes = [saudavel, degradado, critico, morto]
        colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
        explode = (0.05, 0, 0, 0.05)

        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                            startangle=90, colors=colors, explode=explode,
                                            wedgeprops=dict(width=0.4, edgecolor='white'))

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)

        plt.title('Saúde Geral da Frota (Comunicação GSM)', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '06_rosca_saude_geral.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 6 salvo: {caminho}")

    # =========================================================================
    # 7. COLUNAS - MODELOS CRÍTICOS (SEM COMUNICAÇÃO RECENTE)
    # =========================================================================

    def grafico_7_modelos_criticos(self):
        """Gráfico de colunas mostrando modelos com mais equipamentos sem comunicação."""
        fig, ax = plt.subplots(figsize=(12, 7))

        # Calcula equipamentos críticos (8-15 + +16)
        self.df_modelo['Críticos'] = (self.df_modelo['Posição GSM 8-15'] + 
                                      self.df_modelo['Posição GSM +16'])

        # Top 10 modelos críticos
        df_criticos = self.df_modelo.nlargest(10, 'Críticos')

        x = range(len(df_criticos))
        ax.bar(x, df_criticos['Críticos'], color='#e74c3c', alpha=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(df_criticos['Modelo de HW'], rotation=45, ha='right')
        ax.set_xlabel('Modelo de HW', fontsize=12, fontweight='bold')
        ax.set_ylabel('Quantidade de Equipamentos Críticos', fontsize=12, fontweight='bold')

        plt.title('Top 10 Modelos com Mais Equipamentos Sem Comunicação Recente', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '07_modelos_criticos.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 7 salvo: {caminho}")

    # =========================================================================
    # 8. BARRAS - ESPERADO VS ENCONTRADO (TECNOLOGIAS)
    # =========================================================================

    def grafico_8_esperado_vs_encontrado(self):
        """Gráfico comparando esperado vs encontrado por tecnologia."""
        # Nota: Este gráfico precisa de dados da aba "Tipo de Comunicação"
        # Como não temos essa aba no exemplo, vamos simular com dados agregados

        fig, ax = plt.subplots(figsize=(10, 6))

        tecnologias = ['GSM', 'LoRaWAN', 'P2P']

        # Soma das colunas de cada tecnologia
        gsm_encontrado = self.df_modelo['Posição GSM Hoje'].sum() + \
                        self.df_modelo['Posição GSM 1-7'].sum() + \
                        self.df_modelo['Posição GSM 8-15'].sum() + \
                        self.df_modelo['Posição GSM +16'].sum()

        lorawan_encontrado = self.df_modelo['Posição LoRaWAN Hoje'].sum() + \
                            self.df_modelo['Posição LoRaWAN 1-7'].sum() + \
                            self.df_modelo['Posição LoRaWAN 8-15'].sum() + \
                            self.df_modelo['Posição LoRaWAN +16'].sum()

        p2p_encontrado = self.df_modelo['Posição P2P Hoje'].sum() + \
                        self.df_modelo['Posição P2P 1-7'].sum() + \
                        self.df_modelo['Posição P2P 8-15'].sum() + \
                        self.df_modelo['Posição P2P +16'].sum()

        encontrado = [gsm_encontrado, lorawan_encontrado, p2p_encontrado]

        # Esperado (simulado como 110% do encontrado para exemplo)
        esperado = [e * 1.1 for e in encontrado]

        x = np.arange(len(tecnologias))
        width = 0.35

        ax.bar(x - width/2, encontrado, width, label='Encontrado', color='steelblue')
        ax.bar(x + width/2, esperado, width, label='Esperado', color='lightgray')

        ax.set_xticks(x)
        ax.set_xticklabels(tecnologias)
        ax.set_xlabel('Tecnologia', fontsize=12, fontweight='bold')
        ax.set_ylabel('Quantidade de Equipamentos', fontsize=12, fontweight='bold')
        ax.legend()

        plt.title('Esperado vs Encontrado por Tecnologia', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '08_esperado_vs_encontrado.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 8 salvo: {caminho}")

    # =========================================================================
    # 9. BARRAS EMPILHADAS - MULTITECNOLOGIA POR MODELO
    # =========================================================================

    def grafico_9_multitecnologia_modelo(self):
        """Barras empilhadas mostrando uso de múltiplas tecnologias por modelo."""
        fig, ax = plt.subplots(figsize=(12, 10))

        # Top 10 modelos
        top_modelos = self.df_modelo.nlargest(10, 'Quantidade encontrada')

        modelos = top_modelos['Modelo de HW']

        # Soma por tecnologia
        gsm = (top_modelos['Posição GSM Hoje'] + top_modelos['Posição GSM 1-7'] + 
               top_modelos['Posição GSM 8-15'] + top_modelos['Posição GSM +16'])

        lorawan = (top_modelos['Posição LoRaWAN Hoje'] + top_modelos['Posição LoRaWAN 1-7'] + 
                   top_modelos['Posição LoRaWAN 8-15'] + top_modelos['Posição LoRaWAN +16'])

        p2p = (top_modelos['Posição P2P Hoje'] + top_modelos['Posição P2P 1-7'] + 
               top_modelos['Posição P2P 8-15'] + top_modelos['Posição P2P +16'])

        y_pos = np.arange(len(modelos))

        ax.barh(y_pos, gsm, label='GSM', color='#3498db')
        ax.barh(y_pos, lorawan, left=gsm, label='LoRaWAN', color='#9b59b6')
        ax.barh(y_pos, p2p, left=gsm+lorawan, label='P2P', color='#1abc9c')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(modelos)
        ax.set_xlabel('Quantidade de Equipamentos', fontsize=12, fontweight='bold')
        ax.set_ylabel('Modelo de HW', fontsize=12, fontweight='bold')
        ax.legend(loc='lower right')

        plt.title('Uso de Múltiplas Tecnologias por Modelo (Top 10)', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '09_multitecnologia_modelo.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 9 salvo: {caminho}")

    # =========================================================================
    # 10. DISPERSÃO - CORRELAÇÃO MODELO X TEMPO SEM POSIÇÃO
    # =========================================================================

    def grafico_10_dispersao_tempo_sem_posicao(self):
        """Gráfico de dispersão mostrando modelos vs tempo sem posição."""
        fig, ax = plt.subplots(figsize=(12, 8))

        # Calcula "dias médios sem posição" ponderado
        self.df_modelo['Dias_Medio_Sem_Posicao'] = (
            (self.df_modelo['Posição GSM Hoje'] * 0) +
            (self.df_modelo['Posição GSM 1-7'] * 4) +  # média de 1-7 = 4 dias
            (self.df_modelo['Posição GSM 8-15'] * 11.5) +  # média de 8-15 = 11.5 dias
            (self.df_modelo['Posição GSM +16'] * 20)  # assumindo 20 dias
        ) / self.df_modelo['Quantidade encontrada']

        # Plot
        scatter = ax.scatter(self.df_modelo.index, 
                            self.df_modelo['Dias_Medio_Sem_Posicao'],
                            s=self.df_modelo['Quantidade encontrada']*2,
                            alpha=0.6,
                            c=self.df_modelo['Dias_Medio_Sem_Posicao'],
                            cmap='RdYlGn_r')

        # Anotações para modelos críticos
        criticos = self.df_modelo.nlargest(5, 'Dias_Medio_Sem_Posicao')
        for idx, row in criticos.iterrows():
            ax.annotate(row['Modelo de HW'], 
                       (idx, row['Dias_Medio_Sem_Posicao']),
                       fontsize=9, ha='right')

        ax.set_xlabel('Índice do Modelo', fontsize=12, fontweight='bold')
        ax.set_ylabel('Dias Médios Sem Posição', fontsize=12, fontweight='bold')

        plt.colorbar(scatter, label='Dias Médios Sem Posição')
        plt.title('Correlação: Modelo vs Tempo Sem Posição GSM', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '10_dispersao_tempo_sem_posicao.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 10 salvo: {caminho}")

    # =========================================================================
    # 11. BARRAS INVERTIDAS - RANKING DE MODELOS CRÍTICOS
    # =========================================================================

    def grafico_11_ranking_criticidade(self):
        """Ranking de modelos por criticidade."""
        fig, ax = plt.subplots(figsize=(10, 12))

        # Calcula índice de criticidade
        self.df_modelo['Criticidade'] = (
            (self.df_modelo['Posição GSM 8-15'] + self.df_modelo['Posição GSM +16']) / 
            self.df_modelo['Quantidade encontrada'] * 100
        )

        # Top 15 mais críticos
        df_criticos = self.df_modelo.nlargest(15, 'Criticidade')

        y_pos = np.arange(len(df_criticos))

        # Cores baseadas em criticidade
        colors = plt.cm.Reds(df_criticos['Criticidade'] / df_criticos['Criticidade'].max())

        ax.barh(y_pos, df_criticos['Criticidade'], color=colors)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df_criticos['Modelo de HW'])
        ax.set_xlabel('Índice de Criticidade (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Modelo de HW', fontsize=12, fontweight='bold')
        ax.invert_yaxis()

        plt.title('Ranking: Modelos Mais Críticos (% sem comunicação recente)', 
                  fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        caminho = os.path.join(self.output_dir, '11_ranking_criticidade.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 11 salvo: {caminho}")

    # =========================================================================
    # 12. DASHBOARD EXECUTIVO (4 GRÁFICOS EM 1)
    # =========================================================================

    def grafico_12_dashboard_executivo(self):
        """Dashboard executivo com 4 visualizações principais."""
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

        # 1. Rosca - Saúde Geral
        ax1 = fig.add_subplot(gs[0, 0])
        saudavel = self.df_modelo['Posição GSM Hoje'].sum()
        degradado = self.df_modelo['Posição GSM 1-7'].sum()
        critico = self.df_modelo['Posição GSM 8-15'].sum()
        morto = self.df_modelo['Posição GSM +16'].sum()

        sizes = [saudavel, degradado, critico, morto]
        colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
        labels = ['Hoje', '1-7d', '8-15d', '+16d']

        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors,
                wedgeprops=dict(width=0.4))
        ax1.set_title('Saúde Geral da Frota', fontweight='bold')

        # 2. Barras - Top 5 Modelos
        ax2 = fig.add_subplot(gs[0, 1])
        top5 = self.df_modelo.nlargest(5, 'Quantidade encontrada')
        ax2.barh(range(len(top5)), top5['Quantidade encontrada'], color='steelblue')
        ax2.set_yticks(range(len(top5)))
        ax2.set_yticklabels(top5['Modelo de HW'])
        ax2.invert_yaxis()
        ax2.set_title('Top 5 Modelos (Quantidade)', fontweight='bold')
        ax2.set_xlabel('Quantidade')

        # 3. Barras Empilhadas - Distribuição Períodos (Top 5)
        ax3 = fig.add_subplot(gs[1, 0])
        hoje = top5['Posição GSM Hoje']
        dias_1_7 = top5['Posição GSM 1-7']
        dias_8_15 = top5['Posição GSM 8-15']
        dias_16_mais = top5['Posição GSM +16']

        y_pos = np.arange(len(top5))
        ax3.barh(y_pos, hoje, label='Hoje', color='#2ecc71')
        ax3.barh(y_pos, dias_1_7, left=hoje, label='1-7d', color='#f39c12')
        ax3.barh(y_pos, dias_8_15, left=hoje+dias_1_7, label='8-15d', color='#e67e22')
        ax3.barh(y_pos, dias_16_mais, left=hoje+dias_1_7+dias_8_15, label='+16d', color='#e74c3c')

        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(top5['Modelo de HW'])
        ax3.invert_yaxis()
        ax3.legend(loc='lower right', fontsize=8)
        ax3.set_title('Distribuição de Recência (Top 5)', fontweight='bold')
        ax3.set_xlabel('Quantidade')

        # 4. Ranking Criticidade (Top 5)
        ax4 = fig.add_subplot(gs[1, 1])
        self.df_modelo['Criticidade'] = (
            (self.df_modelo['Posição GSM 8-15'] + self.df_modelo['Posição GSM +16']) / 
            self.df_modelo['Quantidade encontrada'] * 100
        )
        top5_criticos = self.df_modelo.nlargest(5, 'Criticidade')

        colors_crit = plt.cm.Reds(top5_criticos['Criticidade'] / top5_criticos['Criticidade'].max())
        ax4.barh(range(len(top5_criticos)), top5_criticos['Criticidade'], color=colors_crit)
        ax4.set_yticks(range(len(top5_criticos)))
        ax4.set_yticklabels(top5_criticos['Modelo de HW'])
        ax4.invert_yaxis()
        ax4.set_title('Top 5 Modelos Críticos', fontweight='bold')
        ax4.set_xlabel('Criticidade (%)')

        fig.suptitle('Dashboard Executivo - Análise de Frota', 
                     fontsize=18, fontweight='bold', y=0.98)

        caminho = os.path.join(self.output_dir, '12_dashboard_executivo.png')
        plt.savefig(caminho, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico 12 salvo: {caminho}")

    # =========================================================================
    # MENU INTERATIVO
    # =========================================================================

    def menu_interativo(self):
        """Menu interativo para escolher quais gráficos gerar."""
        print("\n" + "="*70)
        print("  GERADOR DE GRÁFICOS - RELATÓRIO DE ÚLTIMA POSIÇÃO")
        print("="*70)
        print("\nEscolha quais gráficos deseja gerar:\n")

        opcoes = {
            '1': ('Pareto por Modelo', self.grafico_1_pareto_modelos),
            '2': ('Heatmap de Recência GSM', self.grafico_2_heatmap_recencia),
            '3': ('Barras Empilhadas - Distribuição GSM', self.grafico_3_barras_empilhadas_gsm),
            '4': ('Radar Chart - Perfil de Saúde GSM', self.grafico_4_radar_saude_gsm),
            '5': ('Rosca - Distribuição de Modelos', self.grafico_5_rosca_distribuicao_modelos),
            '6': ('Rosca - Saúde Geral', self.grafico_6_rosca_saude_geral),
            '7': ('Colunas - Modelos Críticos', self.grafico_7_modelos_criticos),
            '8': ('Barras - Esperado vs Encontrado', self.grafico_8_esperado_vs_encontrado),
            '9': ('Barras Empilhadas - Multitecnologia', self.grafico_9_multitecnologia_modelo),
            '10': ('Dispersão - Tempo Sem Posição', self.grafico_10_dispersao_tempo_sem_posicao),
            '11': ('Ranking de Criticidade', self.grafico_11_ranking_criticidade),
            '12': ('Dashboard Executivo (4 em 1)', self.grafico_12_dashboard_executivo),
        }

        for key, (nome, _) in opcoes.items():
            print(f"  [{key}] {nome}")

        print("\n  [0] Gerar TODOS os gráficos")
        print("  [q] Sair\n")

        escolha = input("Digite os números separados por vírgula (ex: 1,3,5) ou 0 para todos: ").strip()

        if escolha.lower() == 'q':
            print("👋 Saindo...")
            return

        if escolha == '0':
            print("\n🚀 Gerando todos os gráficos...\n")
            for _, func in opcoes.values():
                func()
        else:
            numeros = [n.strip() for n in escolha.split(',')]
            print(f"\n🚀 Gerando gráficos selecionados...\n")
            for num in numeros:
                if num in opcoes:
                    opcoes[num][1]()
                else:
                    print(f"⚠️ Opção '{num}' inválida, ignorando...")

        print(f"\n✅ Gráficos salvos em: {os.path.abspath(self.output_dir)}")
        print("="*70 + "\n")

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    # Caminho do arquivo Excel
    arquivo = "resumo_modelo_HW.xlsx"

    # Verifica se arquivo existe
    if not os.path.exists(arquivo):
        print(f"❌ Arquivo '{arquivo}' não encontrado!")
        print("Por favor, coloque o arquivo Excel no mesmo diretório deste script.")
        exit(1)

    # Cria gerador
    gerador = GeradorGraficosRelatorio(arquivo, aba_modelo_hw="Planilha1")

    # Exibe menu interativo
    gerador.menu_interativo()
