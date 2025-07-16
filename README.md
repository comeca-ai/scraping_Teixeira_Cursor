# 🏠 Scraper Imóveis Teixeira de Carvalho

Um sistema completo de extração e análise de dados imobiliários do site [www.teixeiradecarvalho.com.br](https://www.teixeiradecarvalho.com.br).

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Dados Extraídos](#-dados-extraídos)
- [Dashboard](#-dashboard)
- [Arquivos Gerados](#-arquivos-gerados)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Notas Importantes](#-notas-importantes)

## 🎯 Visão Geral

Este projeto realiza o scraping automatizado de **todos os imóveis** disponíveis no site da Teixeira de Carvalho, uma das principais imobiliárias de João Pessoa/PB. O sistema extrai dados completos de cada imóvel, organiza as informações em formatos estruturados (JSON e CSV) e gera um dashboard interativo com análises estatísticas.

## ✨ Funcionalidades

- 🕷️ **Scraping Completo**: Extrai dados de todos os imóveis do site
- 🔄 **Multi-páginas**: Navega automaticamente por todas as páginas de resultados
- 📊 **Múltiplos Formatos**: Salva dados em JSON e CSV
- 📈 **Dashboard Interativo**: Gera visualizações com gráficos interativos
- 🔍 **Análises Estatísticas**: Preços médios por bairro, tipos de imóveis, etc.
- 💾 **Sistema de Backup**: Salva dados periodicamente durante a extração
- 📝 **Logs Detalhados**: Registra todo o processo de extração
- 🛡️ **Tratamento de Erros**: Retry automático e handling de exceções

## 📁 Estrutura do Projeto

```
projeto/
├── main.py                           # Script principal com menu interativo
├── scraper_teixeira_carvalho.py      # Classe principal de scraping
├── dashboard_generator.py            # Gerador de dashboard HTML
├── requirements.txt                  # Dependências Python
├── README.md                         # Esta documentação
├── imoveis_teixeira_carvalho.json    # Dados extraídos (JSON)
├── imoveis_teixeira_carvalho.csv     # Dados extraídos (CSV)
├── dashboard_imoveis.html            # Dashboard interativo
└── scraper_log.log                   # Logs de execução
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou baixe os arquivos do projeto**

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o script principal**:
   ```bash
   python main.py
   ```

## 🔧 Como Usar

### Opção 1: Menu Interativo (Recomendado)

Execute o script principal e escolha uma das opções:

```bash
python main.py
```

**Menu de opções:**
- `1` - Executar apenas o scraping
- `2` - Gerar dashboard (com dados existentes)
- `3` - Processo completo (scraping + dashboard)
- `4` - Verificar status dos arquivos
- `5` - Sair

### Opção 2: Execução Individual

**Apenas scraping:**
```bash
python scraper_teixeira_carvalho.py
```

**Apenas dashboard:**
```bash
python dashboard_generator.py
```

## 📊 Dados Extraídos

Para cada imóvel, o sistema extrai as seguintes informações:

### 🏘️ Informações Básicas
- **URL**: Link direto para o imóvel
- **Código**: Código de referência do imóvel
- **Título**: Título/nome do imóvel
- **Tipo**: Apartamento, Casa, Comercial, Terreno, etc.
- **Operação**: Aluguel ou Venda

### 💰 Informações Financeiras
- **Preço**: Valor principal
- **Preço Original**: Valor original (quando em promoção)

### 📍 Localização
- **Endereço**: Endereço completo
- **Bairro**: Bairro do imóvel
- **Cidade**: Cidade (normalmente João Pessoa)
- **Estado**: Estado (PB)

### 🏠 Características Físicas
- **Área Útil**: Área em m²
- **Área Total**: Área total quando disponível
- **Dormitórios**: Número de quartos
- **Suítes**: Número de suítes
- **Banheiros**: Número de banheiros
- **Vagas de Garagem**: Número de vagas

### 📋 Informações Adicionais
- **Descrição**: Descrição detalhada do imóvel
- **Características**: Lista de características especiais
- **Comodidades**: Lista de comodidades do condomínio
- **Imagens**: URLs das fotos do imóvel
- **Data de Coleta**: Timestamp da extração

## 📈 Dashboard

O dashboard HTML gerado inclui:

### 📊 Estatísticas Resumo
- Total de imóveis coletados
- Número de bairros e tipos
- Preços médios e medianos
- Distribuição por operação (aluguel/venda)

### 📉 Visualizações Interativas
- **Distribuição de Preços**: Histograma dos valores
- **Análise por Bairro**: Top bairros e preços médios
- **Tipos de Imóveis**: Distribuição e preços por categoria
- **Características**: Análise de dormitórios, áreas, etc.
- **Preço por m²**: Análise de valor por metro quadrado
- **Correlações**: Relação entre área e preço

### 🎨 Interface
- Design moderno e responsivo
- Gráficos interativos (zoom, hover, filtros)
- Cores e layout profissional
- Compatível com todos os navegadores

## 📁 Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `imoveis_teixeira_carvalho.json` | Dados estruturados em formato JSON |
| `imoveis_teixeira_carvalho.csv` | Dados tabulares em formato CSV |
| `dashboard_imoveis.html` | Dashboard interativo |
| `scraper_log.log` | Logs detalhados da execução |
| `imoveis_backup.json/csv` | Backups automáticos |

## 🛠️ Tecnologias Utilizadas

- **Python 3.7+**: Linguagem principal
- **Requests**: Requisições HTTP
- **BeautifulSoup4**: Parsing HTML
- **Pandas**: Manipulação de dados
- **Plotly**: Visualizações interativas
- **Logging**: Sistema de logs
- **JSON/CSV**: Formatos de saída

## ⚠️ Notas Importantes

### 🤖 Uso Responsável
- O scraping é feito de forma respeitosa com delays entre requisições
- Não sobrecarrega o servidor do site
- Segue boas práticas de web scraping

### 🔄 Atualizações
- O site pode alterar sua estrutura, requerendo ajustes no código
- Execute periodicamente para obter dados atualizados
- Verifique os logs em caso de problemas

### 💾 Performance
- O tempo de execução varia conforme o número de imóveis
- Sistema de backup salva dados a cada 50 imóveis processados
- Possível interromper e retomar o processo

### 📋 Dados
- Alguns campos podem estar vazios se não disponíveis no site
- O sistema trata automaticamente dados ausentes ou malformados
- Validação automática de tipos de dados

## 🎯 Casos de Uso

Este sistema é ideal para:

- 📊 **Análises de Mercado**: Estudar tendências imobiliárias
- 💼 **Pesquisa Financeira**: Avaliar preços e investimentos
- 🏘️ **Estudos de Bairro**: Comparar regiões e preços
- 📈 **Business Intelligence**: Dashboards para tomada de decisão
- 🎓 **Pesquisas Acadêmicas**: Dados para estudos sobre mercado imobiliário

---

**⚡ Desenvolvido para extrair e analisar dados imobiliários de forma eficiente e organizada!**