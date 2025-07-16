import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import logging
from urllib.parse import urljoin, urlparse
import pandas as pd
from typing import List, Dict, Any
import re
from datetime import datetime

class TeixeiraCarvalhoScraper:
    """
    Scraper para extrair dados de imóveis do site da Teixeira de Carvalho
    """
    
    def __init__(self):
        self.base_url = "https://www.teixeiradecarvalho.com.br"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper_log.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.imoveis_data = []
        
    def get_page(self, url: str, retries: int = 3) -> BeautifulSoup:
        """
        Obter uma página web com tratamento de erros e retry
        """
        for attempt in range(retries):
            try:
                self.logger.info(f"Acessando: {url} (tentativa {attempt + 1})")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                self.logger.warning(f"Erro ao acessar {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                else:
                    self.logger.error(f"Falha ao acessar {url} após {retries} tentativas")
                    return None
    
    def extract_property_urls(self, base_search_url: str) -> List[str]:
        """
        Extrair URLs de todos os imóveis das páginas de busca
        """
        property_urls = []
        page = 1
        
        while True:
            search_url = f"{base_search_url}?pagina={page}"
            soup = self.get_page(search_url)
            
            if not soup:
                break
                
            # Procurar links de imóveis individuais
            property_links = soup.find_all('a', href=re.compile(r'/imovel/'))
            
            if not property_links:
                self.logger.info(f"Nenhum imóvel encontrado na página {page}. Finalizando busca.")
                break
                
            for link in property_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in property_urls:
                        property_urls.append(full_url)
            
            self.logger.info(f"Página {page}: {len(property_links)} imóveis encontrados")
            page += 1
            time.sleep(1)  # Respeitar o servidor
            
        return property_urls
    
    def extract_property_details(self, property_url: str) -> Dict[str, Any]:
        """
        Extrair detalhes de um imóvel específico
        """
        soup = self.get_page(property_url)
        if not soup:
            return None
            
        property_data = {
            'url': property_url,
            'codigo': '',
            'titulo': '',
            'tipo': '',
            'operacao': '',
            'preco': '',
            'preco_original': '',
            'descricao': '',
            'endereco': '',
            'bairro': '',
            'cidade': '',
            'estado': '',
            'area_util': '',
            'area_total': '',
            'dormitorios': '',
            'suites': '',
            'banheiros': '',
            'vagas_garagem': '',
            'caracteristicas': [],
            'comodidades': [],
            'imagens': [],
            'contato': '',
            'data_coleta': datetime.now().isoformat()
        }
        
        try:
            # Código do imóvel
            codigo_elem = soup.find('span', string=re.compile(r'Cód\.|Código'))
            if codigo_elem:
                property_data['codigo'] = re.search(r'\d+', codigo_elem.get_text()).group()
            
            # Título
            title_selectors = ['h1', '.titulo-imovel', '.property-title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    property_data['titulo'] = title_elem.get_text(strip=True)
                    break
            
            # Tipo de operação (aluguel/venda)
            if 'aluguel' in property_url.lower() or 'alugar' in property_url.lower():
                property_data['operacao'] = 'Aluguel'
            elif 'venda' in property_url.lower() or 'comprar' in property_url.lower():
                property_data['operacao'] = 'Venda'
            
            # Preço
            price_selectors = ['.preco', '.price', '.valor', '[class*="preco"]', '[class*="price"]']
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    property_data['preco'] = price_text
                    break
            
            # Preço riscado (original)
            original_price_elem = soup.find(['del', 's', 'strike', '.price-old'])
            if original_price_elem:
                property_data['preco_original'] = original_price_elem.get_text(strip=True)
            
            # Endereço e localização
            address_selectors = ['.endereco', '.address', '.localizacao', '[class*="endereco"]']
            for selector in address_selectors:
                address_elem = soup.select_one(selector)
                if address_elem:
                    address_text = address_elem.get_text(strip=True)
                    property_data['endereco'] = address_text
                    # Extrair bairro e cidade
                    if '-' in address_text:
                        parts = address_text.split('-')
                        if len(parts) >= 2:
                            property_data['bairro'] = parts[0].strip()
                            location = parts[1].strip()
                            if '/' in location:
                                city_state = location.split('/')
                                property_data['cidade'] = city_state[0].strip()
                                if len(city_state) > 1:
                                    property_data['estado'] = city_state[1].strip()
                    break
            
            # Características numéricas (dormitórios, banheiros, etc.)
            characteristics = soup.find_all(['span', 'div'], string=re.compile(r'\d+\s*(Dorm|Suite|Banho|Garagem|m²)'))
            for char in characteristics:
                text = char.get_text(strip=True)
                if 'Dorm' in text:
                    property_data['dormitorios'] = re.search(r'\d+', text).group()
                elif 'Suite' in text:
                    property_data['suites'] = re.search(r'\d+', text).group()
                elif 'Banho' in text:
                    property_data['banheiros'] = re.search(r'\d+', text).group()
                elif 'Garagem' in text:
                    property_data['vagas_garagem'] = re.search(r'\d+', text).group()
                elif 'm²' in text:
                    area_match = re.search(r'\d+', text)
                    if area_match:
                        if not property_data['area_util']:
                            property_data['area_util'] = area_match.group()
                        else:
                            property_data['area_total'] = area_match.group()
            
            # Descrição
            desc_selectors = ['.descricao', '.description', '.texto-imovel']
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    property_data['descricao'] = desc_elem.get_text(strip=True)
                    break
            
            # Características/comodidades
            features_lists = soup.find_all(['ul', 'div'], class_=re.compile(r'caracteristicas|comodidades|features'))
            for features_list in features_lists:
                items = features_list.find_all(['li', 'span', 'div'])
                for item in items:
                    feature_text = item.get_text(strip=True)
                    if feature_text and len(feature_text) > 2:
                        property_data['caracteristicas'].append(feature_text)
            
            # Imagens
            img_elements = soup.find_all('img', src=re.compile(r'\.(jpg|jpeg|png|gif)', re.I))
            for img in img_elements:
                src = img.get('src')
                if src:
                    full_img_url = urljoin(property_url, src)
                    property_data['imagens'].append(full_img_url)
            
            # Tipo de imóvel (tentativa de detecção)
            title_lower = property_data['titulo'].lower()
            if 'apartamento' in title_lower:
                property_data['tipo'] = 'Apartamento'
            elif 'casa' in title_lower:
                property_data['tipo'] = 'Casa'
            elif 'comercial' in title_lower:
                property_data['tipo'] = 'Comercial'
            elif 'terreno' in title_lower:
                property_data['tipo'] = 'Terreno'
            elif 'flat' in title_lower:
                property_data['tipo'] = 'Flat'
            elif 'studio' in title_lower or 'estúdio' in title_lower:
                property_data['tipo'] = 'Studio'
                
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados de {property_url}: {e}")
            
        return property_data
    
    def scrape_all_properties(self):
        """
        Fazer scraping de todos os imóveis
        """
        # URLs das diferentes categorias
        search_urls = [
            f"{self.base_url}/busca-avanc",  # Busca geral
            f"{self.base_url}/imoveis/para-alugar",  # Aluguel
            f"{self.base_url}/imoveis/para-comprar",  # Venda
            f"{self.base_url}/lancamentos"  # Lançamentos
        ]
        
        all_property_urls = set()
        
        # Coletar URLs de todas as categorias
        for search_url in search_urls:
            self.logger.info(f"Coletando URLs de: {search_url}")
            urls = self.extract_property_urls(search_url)
            all_property_urls.update(urls)
            time.sleep(2)
        
        self.logger.info(f"Total de {len(all_property_urls)} imóveis únicos encontrados")
        
        # Extrair dados de cada imóvel
        for i, property_url in enumerate(all_property_urls, 1):
            self.logger.info(f"Processando imóvel {i}/{len(all_property_urls)}: {property_url}")
            property_data = self.extract_property_details(property_url)
            
            if property_data:
                self.imoveis_data.append(property_data)
                
            # Pausa entre requisições para não sobrecarregar o servidor
            time.sleep(1.5)
            
            # Salvar dados a cada 50 imóveis processados
            if i % 50 == 0:
                self.save_data_backup()
    
    def save_data_backup(self):
        """
        Salvar backup dos dados coletados
        """
        if self.imoveis_data:
            # Salvar JSON
            with open('imoveis_backup.json', 'w', encoding='utf-8') as f:
                json.dump(self.imoveis_data, f, ensure_ascii=False, indent=2)
            
            # Salvar CSV
            df = pd.DataFrame(self.imoveis_data)
            df.to_csv('imoveis_backup.csv', index=False, encoding='utf-8')
            
            self.logger.info(f"Backup salvo com {len(self.imoveis_data)} imóveis")
    
    def save_final_data(self):
        """
        Salvar dados finais em JSON e CSV
        """
        if not self.imoveis_data:
            self.logger.warning("Nenhum dado coletado para salvar")
            return
        
        # Salvar JSON
        with open('imoveis_teixeira_carvalho.json', 'w', encoding='utf-8') as f:
            json.dump(self.imoveis_data, f, ensure_ascii=False, indent=2)
        
        # Converter listas para strings no CSV
        data_for_csv = []
        for imovel in self.imoveis_data:
            imovel_csv = imovel.copy()
            for key, value in imovel_csv.items():
                if isinstance(value, list):
                    imovel_csv[key] = '; '.join(map(str, value))
            data_for_csv.append(imovel_csv)
        
        # Salvar CSV
        df = pd.DataFrame(data_for_csv)
        df.to_csv('imoveis_teixeira_carvalho.csv', index=False, encoding='utf-8')
        
        self.logger.info(f"Dados finais salvos: {len(self.imoveis_data)} imóveis")
        
        # Estatísticas
        self.print_statistics()
    
    def print_statistics(self):
        """
        Imprimir estatísticas dos dados coletados
        """
        if not self.imoveis_data:
            return
        
        df = pd.DataFrame(self.imoveis_data)
        
        print("\n" + "="*50)
        print("ESTATÍSTICAS DOS DADOS COLETADOS")
        print("="*50)
        print(f"Total de imóveis: {len(self.imoveis_data)}")
        
        if 'operacao' in df.columns:
            print(f"\nPor operação:")
            print(df['operacao'].value_counts())
        
        if 'tipo' in df.columns:
            print(f"\nPor tipo:")
            print(df['tipo'].value_counts())
        
        if 'bairro' in df.columns:
            print(f"\nTop 10 bairros:")
            print(df['bairro'].value_counts().head(10))
        
        print("\n" + "="*50)

def main():
    """
    Função principal para executar o scraping
    """
    scraper = TeixeiraCarvalhoScraper()
    
    try:
        print("Iniciando scraping do site Teixeira de Carvalho...")
        scraper.scrape_all_properties()
        scraper.save_final_data()
        print("Scraping concluído com sucesso!")
        
    except KeyboardInterrupt:
        print("\nScraping interrompido pelo usuário")
        scraper.save_data_backup()
    except Exception as e:
        print(f"Erro durante o scraping: {e}")
        scraper.save_data_backup()
    
if __name__ == "__main__":
    main()