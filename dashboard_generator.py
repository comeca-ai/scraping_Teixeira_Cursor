import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime
import re

class DashboardGenerator:
    """
    Gerador de dashboard HTML com análises dos dados de imóveis
    """
    
    def __init__(self, json_file='imoveis_teixeira_carvalho.json'):
        self.json_file = json_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """
        Carregar dados do arquivo JSON
        """
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.df = pd.DataFrame(data)
            print(f"Dados carregados: {len(self.df)} imóveis")
            self.clean_data()
            
        except FileNotFoundError:
            print(f"Arquivo {self.json_file} não encontrado. Execute primeiro o scraping.")
            self.df = pd.DataFrame()
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            self.df = pd.DataFrame()
    
    def clean_data(self):
        """
        Limpar e preparar os dados para análise
        """
        if self.df.empty:
            return
        
        # Limpar preços - extrair apenas números
        def clean_price(price_str):
            if pd.isna(price_str) or price_str == '':
                return None
            # Remover tudo exceto números e pontos/vírgulas
            price_clean = re.sub(r'[^\d.,]', '', str(price_str))
            # Substituir vírgulas por pontos
            price_clean = price_clean.replace(',', '.')
            # Tentar converter para float
            try:
                return float(price_clean)
            except:
                return None
        
        self.df['preco_numerico'] = self.df['preco'].apply(clean_price)
        
        # Limpar área
        def clean_area(area_str):
            if pd.isna(area_str) or area_str == '':
                return None
            area_clean = re.sub(r'[^\d.]', '', str(area_str))
            try:
                return float(area_clean)
            except:
                return None
        
        self.df['area_numerica'] = self.df['area_util'].apply(clean_area)
        
        # Limpar campos numéricos
        for col in ['dormitorios', 'suites', 'banheiros', 'vagas_garagem']:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Calcular preço por m²
        self.df['preco_por_m2'] = self.df['preco_numerico'] / self.df['area_numerica']
        
        # Preencher valores vazios
        self.df['bairro'] = self.df['bairro'].fillna('Não informado')
        self.df['tipo'] = self.df['tipo'].fillna('Não informado')
        self.df['operacao'] = self.df['operacao'].fillna('Não informado')
    
    def create_price_distribution_chart(self):
        """
        Criar gráfico de distribuição de preços
        """
        df_with_price = self.df[self.df['preco_numerico'].notna()]
        
        if df_with_price.empty:
            return go.Figure().add_annotation(text="Dados de preço não disponíveis", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        fig = px.histogram(df_with_price, x='preco_numerico', 
                          title='Distribuição de Preços dos Imóveis',
                          labels={'preco_numerico': 'Preço (R$)', 'count': 'Quantidade'},
                          nbins=30)
        
        fig.update_layout(
            xaxis_title="Preço (R$)",
            yaxis_title="Quantidade de Imóveis",
            title_x=0.5
        )
        
        return fig
    
    def create_neighborhood_analysis(self):
        """
        Criar análise por bairro
        """
        # Top 10 bairros com mais imóveis
        neighborhood_counts = self.df['bairro'].value_counts().head(10)
        
        fig1 = px.bar(x=neighborhood_counts.values, y=neighborhood_counts.index,
                     title='Top 10 Bairros com Mais Imóveis',
                     labels={'x': 'Quantidade de Imóveis', 'y': 'Bairro'},
                     orientation='h')
        fig1.update_layout(title_x=0.5, height=400)
        
        # Preço médio por bairro (top 10)
        df_with_price = self.df[self.df['preco_numerico'].notna()]
        avg_price_by_neighborhood = df_with_price.groupby('bairro')['preco_numerico'].mean().sort_values(ascending=False).head(10)
        
        fig2 = px.bar(x=avg_price_by_neighborhood.index, y=avg_price_by_neighborhood.values,
                     title='Preço Médio por Bairro (Top 10)',
                     labels={'x': 'Bairro', 'y': 'Preço Médio (R$)'})
        fig2.update_layout(title_x=0.5, height=400, xaxis_tickangle=45)
        
        return fig1, fig2
    
    def create_property_type_analysis(self):
        """
        Criar análise por tipo de imóvel
        """
        # Distribuição por tipo
        type_counts = self.df['tipo'].value_counts()
        
        fig1 = px.pie(values=type_counts.values, names=type_counts.index,
                     title='Distribuição por Tipo de Imóvel')
        fig1.update_layout(title_x=0.5)
        
        # Preço médio por tipo
        df_with_price = self.df[self.df['preco_numerico'].notna()]
        avg_price_by_type = df_with_price.groupby('tipo')['preco_numerico'].mean().sort_values(ascending=False)
        
        fig2 = px.bar(x=avg_price_by_type.index, y=avg_price_by_type.values,
                     title='Preço Médio por Tipo de Imóvel',
                     labels={'x': 'Tipo', 'y': 'Preço Médio (R$)'})
        fig2.update_layout(title_x=0.5, height=400)
        
        return fig1, fig2
    
    def create_operation_analysis(self):
        """
        Criar análise por tipo de operação (aluguel/venda)
        """
        operation_counts = self.df['operacao'].value_counts()
        
        fig = px.pie(values=operation_counts.values, names=operation_counts.index,
                    title='Distribuição por Tipo de Operação')
        fig.update_layout(title_x=0.5)
        
        return fig
    
    def create_characteristics_analysis(self):
        """
        Criar análise de características dos imóveis
        """
        # Distribuição de dormitórios
        dorm_counts = self.df['dormitorios'].value_counts().sort_index()
        
        fig1 = px.bar(x=dorm_counts.index, y=dorm_counts.values,
                     title='Distribuição por Número de Dormitórios',
                     labels={'x': 'Número de Dormitórios', 'y': 'Quantidade'})
        fig1.update_layout(title_x=0.5)
        
        # Relação área vs preço
        df_scatter = self.df[(self.df['area_numerica'].notna()) & (self.df['preco_numerico'].notna())]
        
        fig2 = px.scatter(df_scatter, x='area_numerica', y='preco_numerico',
                         color='tipo', title='Relação Área vs Preço',
                         labels={'area_numerica': 'Área (m²)', 'preco_numerico': 'Preço (R$)'})
        fig2.update_layout(title_x=0.5)
        
        return fig1, fig2
    
    def create_price_per_sqm_analysis(self):
        """
        Criar análise de preço por m²
        """
        df_price_sqm = self.df[self.df['preco_por_m2'].notna()]
        
        if df_price_sqm.empty:
            return go.Figure().add_annotation(text="Dados de preço por m² não disponíveis", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        # Preço por m² por bairro
        avg_price_sqm = df_price_sqm.groupby('bairro')['preco_por_m2'].mean().sort_values(ascending=False).head(10)
        
        fig = px.bar(x=avg_price_sqm.index, y=avg_price_sqm.values,
                    title='Preço Médio por m² por Bairro (Top 10)',
                    labels={'x': 'Bairro', 'y': 'Preço por m² (R$)'})
        fig.update_layout(title_x=0.5, xaxis_tickangle=45)
        
        return fig
    
    def generate_summary_statistics(self):
        """
        Gerar estatísticas resumo
        """
        stats = {
            'total_imoveis': len(self.df),
            'tipos_imoveis': self.df['tipo'].nunique(),
            'bairros': self.df['bairro'].nunique(),
            'preco_medio': self.df['preco_numerico'].mean(),
            'preco_mediano': self.df['preco_numerico'].median(),
            'area_media': self.df['area_numerica'].mean(),
            'imoveis_aluguel': len(self.df[self.df['operacao'] == 'Aluguel']),
            'imoveis_venda': len(self.df[self.df['operacao'] == 'Venda']),
        }
        
        return stats
    
    def generate_dashboard(self):
        """
        Gerar dashboard HTML completo
        """
        if self.df.empty:
            print("Nenhum dado disponível para gerar dashboard")
            return
        
        print("Gerando dashboard...")
        
        # Criar gráficos
        price_dist_fig = self.create_price_distribution_chart()
        neighborhood_fig1, neighborhood_fig2 = self.create_neighborhood_analysis()
        type_fig1, type_fig2 = self.create_property_type_analysis()
        operation_fig = self.create_operation_analysis()
        char_fig1, char_fig2 = self.create_characteristics_analysis()
        price_sqm_fig = self.create_price_per_sqm_analysis()
        
        # Estatísticas resumo
        stats = self.generate_summary_statistics()
        
        # Criar HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - Imóveis Teixeira de Carvalho</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .stats-container {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-left: 4px solid #667eea;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .chart-container {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .chart-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                    gap: 30px;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Dashboard de Imóveis</h1>
                <h2>Teixeira de Carvalho</h2>
                <p>Análise completa dos dados coletados em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <div class="stats-container">
                <div class="stat-card">
                    <div class="stat-number">{stats['total_imoveis']:,.0f}</div>
                    <div class="stat-label">Total de Imóveis</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['bairros']}</div>
                    <div class="stat-label">Bairros</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['tipos_imoveis']}</div>
                    <div class="stat-label">Tipos de Imóveis</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">R$ {stats['preco_medio']:,.0f}</div>
                    <div class="stat-label">Preço Médio</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['imoveis_venda']:,.0f}</div>
                    <div class="stat-label">Imóveis à Venda</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['imoveis_aluguel']:,.0f}</div>
                    <div class="stat-label">Imóveis para Aluguel</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div id="price-distribution"></div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-container">
                    <div id="operation-distribution"></div>
                </div>
                <div class="chart-container">
                    <div id="type-distribution"></div>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-container">
                    <div id="neighborhood-count"></div>
                </div>
                <div class="chart-container">
                    <div id="neighborhood-price"></div>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-container">
                    <div id="type-price"></div>
                </div>
                <div class="chart-container">
                    <div id="price-per-sqm"></div>
                </div>
            </div>
            
            <div class="chart-grid">
                <div class="chart-container">
                    <div id="bedrooms-distribution"></div>
                </div>
                <div class="chart-container">
                    <div id="area-vs-price"></div>
                </div>
            </div>
            
            <div class="footer">
                <p>Dashboard gerado automaticamente a partir dos dados coletados do site <strong>www.teixeiradecarvalho.com.br</strong></p>
                <p>Dados coletados em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <script>
                // Renderizar gráficos
                Plotly.newPlot('price-distribution', {price_dist_fig.to_dict()['data']}, {price_dist_fig.to_dict()['layout']});
                Plotly.newPlot('operation-distribution', {operation_fig.to_dict()['data']}, {operation_fig.to_dict()['layout']});
                Plotly.newPlot('type-distribution', {type_fig1.to_dict()['data']}, {type_fig1.to_dict()['layout']});
                Plotly.newPlot('neighborhood-count', {neighborhood_fig1.to_dict()['data']}, {neighborhood_fig1.to_dict()['layout']});
                Plotly.newPlot('neighborhood-price', {neighborhood_fig2.to_dict()['data']}, {neighborhood_fig2.to_dict()['layout']});
                Plotly.newPlot('type-price', {type_fig2.to_dict()['data']}, {type_fig2.to_dict()['layout']});
                Plotly.newPlot('price-per-sqm', {price_sqm_fig.to_dict()['data']}, {price_sqm_fig.to_dict()['layout']});
                Plotly.newPlot('bedrooms-distribution', {char_fig1.to_dict()['data']}, {char_fig1.to_dict()['layout']});
                Plotly.newPlot('area-vs-price', {char_fig2.to_dict()['data']}, {char_fig2.to_dict()['layout']});
            </script>
        </body>
        </html>
        """
        
        # Salvar HTML
        with open('dashboard_imoveis.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("Dashboard salvo como 'dashboard_imoveis.html'")
        print(f"Dashboard gerado com dados de {len(self.df)} imóveis")

def main():
    """
    Função principal para gerar o dashboard
    """
    dashboard = DashboardGenerator()
    dashboard.generate_dashboard()

if __name__ == "__main__":
    main()