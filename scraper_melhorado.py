import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import logging
from urllib.parse import urljoin, urlparse, quote
import pandas as pd
from typing import List, Dict, Any
import re
from datetime import datetime
import random

class TeixeiraCarvalhoScraperMelhorado:
    """
    Scraper melhorado e específico para o site da Teixeira de Carvalho
    """
    
    def __init__(self):
        self.base_url = "https://www.teixeiradecarvalho.com.br"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper_melhorado_log.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.imoveis_data = []
        self.processed_urls = set()
        
    def get_random_delay(self, min_delay=1, max_delay=3):
        """
        Gerar delay aleatório entre requisições
        """
        return random.uniform(min_delay, max_delay)
    
    def get_page(self, url: str, retries: int = 3) -> BeautifulSoup:
        """
        Obter uma página web com tratamento avançado de erros
        """
        for attempt in range(retries):
            try:
                # Delay aleatório para parecer mais humano
                time.sleep(self.get_random_delay())
                
                self.logger.info(f"Acessando: {url} (tentativa {attempt + 1})")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # Verificar se a resposta é válida
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                else:
                    self.logger.warning(f"Status code {response.status_code} para {url}")
                    
            except requests.RequestException as e:
                self.logger.warning(f"Erro ao acessar {url}: {e}")
                if attempt < retries - 1:
                    wait_time = 2 ** attempt + random.uniform(1, 3)
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Falha ao acessar {url} após {retries} tentativas")
                    return None
    
    def discover_property_urls(self) -> List[str]:
        """
        Descobrir URLs de imóveis através de múltiplas estratégias
        """
        all_urls = set()
        
        # Estratégia 1: Página inicial com categorias
        main_page_urls = self.extract_from_main_page()
        all_urls.update(main_page_urls)
        
        # Estratégia 2: Páginas de busca específicas
        search_urls = self.extract_from_search_pages()
        all_urls.update(search_urls)
        
        # Estratégia 3: Sitemap (se disponível)
        sitemap_urls = self.extract_from_sitemap()
        all_urls.update(sitemap_urls)
        
        return list(all_urls)
    
    def extract_from_main_page(self) -> List[str]:
        """
        Extrair URLs da página principal
        """
        self.logger.info("Extraindo URLs da página principal...")
        urls = []
        
        # Acessar página principal
        soup = self.get_page(self.base_url)
        if not soup:
            return urls
        
        # Procurar por links de imóveis na página principal
        property_links = soup.find_all('a', href=True)
        
        for link in property_links:
            href = link.get('href')
            if href and any(keyword in href.lower() for keyword in ['imovel', 'codigo', 'ref']):
                full_url = urljoin(self.base_url, href)
                if self.is_valid_property_url(full_url):
                    urls.append(full_url)
        
        self.logger.info(f"Encontrados {len(urls)} URLs na página principal")
        return urls
    
    def extract_from_search_pages(self) -> List[str]:
        """
        Extrair URLs das páginas de busca
        """
        self.logger.info("Extraindo URLs das páginas de busca...")
        urls = []
        
        # URLs de busca baseadas na estrutura observada
        search_endpoints = [
            "/imoveis",
            "/imoveis/para-alugar",
            "/imoveis/para-comprar", 
            "/imoveis/aluguel",
            "/imoveis/venda",
            "/busca",
            "/busca-avancada",
            "/lancamentos"
        ]
        
        for endpoint in search_endpoints:
            page_urls = self.extract_from_search_endpoint(endpoint)
            urls.extend(page_urls)
            
        return urls
    
    def extract_from_search_endpoint(self, endpoint: str) -> List[str]:
        """
        Extrair URLs de um endpoint específico de busca
        """
        urls = []
        page = 1
        max_pages = 100  # Limite de segurança
        
        while page <= max_pages:
            # Diferentes formatos de paginação possíveis
            page_urls = [
                f"{self.base_url}{endpoint}?pagina={page}",
                f"{self.base_url}{endpoint}?page={page}",
                f"{self.base_url}{endpoint}?p={page}",
                f"{self.base_url}{endpoint}/pagina/{page}",
                f"{self.base_url}{endpoint}/page/{page}"
            ]
            
            found_properties = False
            
            for page_url in page_urls:
                soup = self.get_page(page_url)
                if not soup:
                    continue
                
                # Procurar por cards/links de imóveis
                property_elements = self.find_property_elements(soup)
                
                if property_elements:
                    found_properties = True
                    for element in property_elements:
                        url = self.extract_url_from_element(element)
                        if url and self.is_valid_property_url(url):
                            urls.append(url)
                    break
            
            if not found_properties:
                break
                
            self.logger.info(f"Página {page} de {endpoint}: {len(property_elements) if found_properties else 0} imóveis")
            page += 1
            
        return urls
    
    def find_property_elements(self, soup: BeautifulSoup) -> List:
        """
        Encontrar elementos que representam imóveis na página
        """
        # Múltiplos seletores possíveis baseados em estruturas comuns
        selectors = [
            'div[class*="imovel"]',
            'div[class*="property"]',
            'div[class*="card"]',
            'article[class*="imovel"]',
            'article[class*="property"]',
            '.resultado-busca',
            '.item-imovel',
            '.property-item',
            '.imovel-card',
            'a[href*="imovel"]',
            'a[href*="codigo"]',
            'a[href*="ref"]'
        ]
        
        all_elements = []
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                all_elements.extend(elements)
        
        # Remover duplicatas mantendo ordem
        seen = set()
        unique_elements = []
        for element in all_elements:
            element_html = str(element)
            if element_html not in seen:
                seen.add(element_html)
                unique_elements.append(element)
        
        return unique_elements
    
    def extract_url_from_element(self, element) -> str:
        """
        Extrair URL de um elemento de imóvel
        """
        # Tentar diferentes formas de encontrar o link
        
        # 1. Se o próprio elemento é um link
        if element.name == 'a' and element.get('href'):
            return urljoin(self.base_url, element.get('href'))
        
        # 2. Procurar link dentro do elemento
        link = element.find('a', href=True)
        if link:
            return urljoin(self.base_url, link.get('href'))
        
        # 3. Procurar por atributos data-*
        for attr in element.attrs:
            if 'url' in attr.lower() or 'link' in attr.lower():
                return urljoin(self.base_url, element.get(attr))
        
        return None
    
    def is_valid_property_url(self, url: str) -> bool:
        """
        Verificar se uma URL é válida para um imóvel
        """
        if not url or url in self.processed_urls:
            return False
        
        # Verificar se contém palavras-chave de imóvel
        keywords = ['imovel', 'codigo', 'ref', 'property', 'cod']
        url_lower = url.lower()
        
        if not any(keyword in url_lower for keyword in keywords):
            return False
        
        # Evitar URLs inválidas
        invalid_patterns = ['javascript:', 'mailto:', '#', 'tel:', 'whatsapp']
        
        if any(pattern in url_lower for pattern in invalid_patterns):
            return False
        
        return True
    
    def extract_from_sitemap(self) -> List[str]:
        """
        Tentar extrair URLs do sitemap
        """
        self.logger.info("Tentando acessar sitemap...")
        urls = []
        
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/robots.txt"
        ]
        
        for sitemap_url in sitemap_urls:
            soup = self.get_page(sitemap_url)
            if soup:
                # Procurar por URLs no sitemap
                loc_tags = soup.find_all('loc')
                for loc in loc_tags:
                    url = loc.get_text().strip()
                    if self.is_valid_property_url(url):
                        urls.append(url)
        
        return urls
    
    def extract_property_details(self, property_url: str) -> Dict[str, Any]:
        """
        Extrair detalhes específicos de um imóvel
        """
        if property_url in self.processed_urls:
            return None
            
        self.processed_urls.add(property_url)
        
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
            'preco_condominio': '',
            'preco_iptu': '',
            'descricao': '',
            'endereco': '',
            'bairro': '',
            'cidade': '',
            'estado': '',
            'cep': '',
            'area_util': '',
            'area_total': '',
            'area_terreno': '',
            'dormitorios': '',
            'suites': '',
            'banheiros': '',
            'vagas_garagem': '',
            'andar': '',
            'total_andares': '',
            'idade_imovel': '',
            'caracteristicas': [],
            'comodidades': [],
            'lazer': [],
            'seguranca': [],
            'imagens': [],
            'videos': [],
            'contato_nome': '',
            'contato_telefone': '',
            'contato_email': '',
            'corretor': '',
            'data_coleta': datetime.now().isoformat(),
            'disponivel': True
        }
        
        try:
            # Extrair informações específicas
            self.extract_basic_info(soup, property_data)
            self.extract_price_info(soup, property_data)
            self.extract_location_info(soup, property_data)
            self.extract_physical_info(soup, property_data)
            self.extract_features(soup, property_data)
            self.extract_media(soup, property_data)
            self.extract_contact_info(soup, property_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados de {property_url}: {e}")
        
        return property_data
    
    def extract_basic_info(self, soup: BeautifulSoup, data: Dict):
        """
        Extrair informações básicas do imóvel
        """
        # Código do imóvel
        code_patterns = [
            r'C[óo]d[.:]\s*(\d+)',
            r'Ref[.:]\s*(\d+)',
            r'C[óo]digo[.:]\s*(\d+)'
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                data['codigo'] = match.group(1)
                break
        
        # Título
        title_selectors = [
            'h1',
            '.titulo',
            '.title',
            '.property-title',
            '.imovel-titulo',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                data['titulo'] = element.get_text(strip=True)
                break
        
        # Tipo de operação
        text_content = soup.get_text().lower()
        if 'aluguel' in text_content or 'alugar' in text_content:
            data['operacao'] = 'Aluguel'
        elif 'venda' in text_content or 'comprar' in text_content:
            data['operacao'] = 'Venda'
        elif 'lançamento' in text_content:
            data['operacao'] = 'Lançamento'
        
        # Tipo de imóvel
        title_lower = data['titulo'].lower()
        if 'apartamento' in title_lower or 'apto' in title_lower:
            data['tipo'] = 'Apartamento'
        elif 'casa' in title_lower:
            data['tipo'] = 'Casa'
        elif 'comercial' in title_lower or 'loja' in title_lower or 'sala' in title_lower:
            data['tipo'] = 'Comercial'
        elif 'terreno' in title_lower:
            data['tipo'] = 'Terreno'
        elif 'flat' in title_lower:
            data['tipo'] = 'Flat'
        elif 'studio' in title_lower or 'estúdio' in title_lower:
            data['tipo'] = 'Studio'
        elif 'galpão' in title_lower:
            data['tipo'] = 'Galpão'
        elif 'cobertura' in title_lower:
            data['tipo'] = 'Cobertura'
    
    def extract_price_info(self, soup: BeautifulSoup, data: Dict):
        """
        Extrair informações de preço
        """
        # Padrões de preço
        price_patterns = [
            r'R\$\s*([\d.,]+)',
            r'([\d.,]+)\s*reais?',
            r'Valor[:\s]+R\$\s*([\d.,]+)',
            r'Pre[çc]o[:\s]+R\$\s*([\d.,]+)'
        ]
        
        text_content = soup.get_text()
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                # Pegar o primeiro preço encontrado
                price_str = matches[0]
                data['preco'] = f"R$ {price_str}"
                break
        
        # Procurar preços específicos em elementos
        price_selectors = [
            '.preco',
            '.price',
            '.valor',
            '.money',
            '[class*="preco"]',
            '[class*="price"]',
            '[class*="valor"]'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if 'R$' in text and any(char.isdigit() for char in text):
                    if not data['preco']:
                        data['preco'] = text
                    elif 'condom' in text.lower():
                        data['preco_condominio'] = text
                    elif 'iptu' in text.lower():
                        data['preco_iptu'] = text
    
    def extract_location_info(self, soup: BeautifulSoup, data: Dict):
        """
        Extrair informações de localização
        """
        # Padrões de endereço
        address_patterns = [
            r'([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç\s]+)\s*-\s*([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][a-záàâãéèêíìîóòôõúùûç\s]+)',
            r'Endere[çc]o[:\s]+([^\n]+)',
            r'Localiza[çc][ãa]o[:\s]+([^\n]+)'
        ]
        
        text_content = soup.get_text()
        
        for pattern in address_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                if ' - ' in match.group(0):
                    parts = match.group(0).split(' - ')
                    if len(parts) >= 2:
                        data['bairro'] = parts[0].strip()
                        location = parts[1].strip()
                        if '/' in location:
                            city_state = location.split('/')
                            data['cidade'] = city_state[0].strip()
                            if len(city_state) > 1:
                                data['estado'] = city_state[1].strip()
                        else:
                            data['cidade'] = location
                else:
                    data['endereco'] = match.group(1).strip()
                break
        
        # CEP
        cep_match = re.search(r'(\d{5}-?\d{3})', text_content)
        if cep_match:
            data['cep'] = cep_match.group(1)
    
    def extract_physical_info(self, soup: BeautifulSoup, data: Dict):
        """
        Extrair características físicas
        """
        # Padrões para características numéricas
        patterns = {
            'dormitorios': [r'(\d+)\s*(?:dorm|quarto)', r'(\d+)\s*Dorm'],
            'suites': [r'(\d+)\s*su[íi]te', r'(\d+)\s*Suite'],
            'banheiros': [r'(\d+)\s*banho', r'(\d+)\s*Banho'],
            'vagas_garagem': [r'(\d+)\s*vaga', r'(\d+)\s*Garagem'],
            'area_util': [r'(\d+(?:[.,]\d+)?)\s*m²?\s*(?:útil|util)', r'(\d+(?:[.,]\d+)?)\s*m²\s*A\.\s*Útil'],
            'area_total': [r'(\d+(?:[.,]\d+)?)\s*m²?\s*(?:total)', r'(\d+(?:[.,]\d+)?)\s*m²'],
            'andar': [r'(\d+)[ºo°]?\s*andar', r'Andar[:\s]*(\d+)']
        }
        
        text_content = soup.get_text()
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data[field] = match.group(1)
                    break
    
    def extract_features(self, soup: BeautifulSoup, data: Dict):
        """
        Extrair características e comodidades
        """
        # Procurar listas de características
        feature_lists = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'caracteristicas|features|comodidades|amenities', re.I))
        
        for feature_list in feature_lists:
            items = feature_list.find_all(['li', 'span', 'div', 'p'])
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 2 and len(text) < 100:
                    # Categorizar características
                    text_lower = text.lower()
                    if any(word in text_lower for word in ['piscina', 'academia', 'playground', 'churrasqueira', 'salão']):
                        data['lazer'].append(text)
                    elif any(word in text_lower for word in ['portaria', 'segurança', 'câmera', 'alarme']):
                        data['seguranca'].append(text)
                    elif any(word in text_lower for word in ['ar condicionado', 'armário', 'cozinha', 'banheiro']):
                        data['caracteristicas'].append(text)
                    else:
                        data['comodidades'].append(text)
        
        # Descrição
        desc_selectors = [
            '.descricao',
            '.description',
            '.texto',
            '.content',
            '[class*="descricao"]',
            '[class*="description"]'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                desc_text = element.get_text(strip=True)
                if len(desc_text) > 50:  # Só pegar descrições significativas
                    data['descricao'] = desc_text
                    break
    
    def extract_media(self, soup: BeautifulSoup, data: Dict):
        """
        Extrair imagens e vídeos
        """
        # Imagens
        img_selectors = [
            'img[src*="imovel"]',
            'img[src*="property"]',
            '.gallery img',
            '.fotos img',
            '.images img',
            'img[alt*="imóvel"]',
            'img[alt*="imovel"]'
        ]
        
        for selector in img_selectors:
            images = soup.select(selector)
            for img in images:
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(self.base_url, src)
                    if full_url not in data['imagens']:
                        data['imagens'].append(full_url)
        
        # Vídeos
        video_elements = soup.find_all(['video', 'iframe'])
        for video in video_elements:
            src = video.get('src')
            if src:
                data['videos'].append(urljoin(self.base_url, src))
    
    def extract_contact_info(self, soup: BeautifulSoup, data: Dict):
        """
        Extrair informações de contato
        """
        # Telefones
        phone_pattern = r'(?:\(?\d{2}\)?\s*)?(?:9\s*)?\d{4}[-\s]?\d{4}'
        phones = re.findall(phone_pattern, soup.get_text())
        if phones:
            data['contato_telefone'] = phones[0]
        
        # Email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            data['contato_email'] = emails[0]
        
        # Nome do corretor
        corretor_selectors = [
            '.corretor',
            '.agent',
            '.vendedor',
            '[class*="corretor"]'
        ]
        
        for selector in corretor_selectors:
            element = soup.select_one(selector)
            if element:
                data['corretor'] = element.get_text(strip=True)
                break
    
    def scrape_all_properties(self):
        """
        Executar scraping completo
        """
        self.logger.info("Iniciando descoberta de URLs de imóveis...")
        
        # Descobrir todas as URLs de imóveis
        property_urls = self.discover_property_urls()
        
        # Remover duplicatas
        property_urls = list(set(property_urls))
        
        self.logger.info(f"Total de {len(property_urls)} URLs únicas de imóveis descobertas")
        
        if not property_urls:
            self.logger.warning("Nenhuma URL de imóvel encontrada. Verifique a estrutura do site.")
            return
        
        # Extrair dados de cada imóvel
        for i, property_url in enumerate(property_urls, 1):
            self.logger.info(f"Processando imóvel {i}/{len(property_urls)}: {property_url}")
            
            property_data = self.extract_property_details(property_url)
            
            if property_data:
                self.imoveis_data.append(property_data)
                self.logger.info(f"Dados extraídos com sucesso para: {property_data.get('titulo', 'Sem título')}")
            else:
                self.logger.warning(f"Falha ao extrair dados de: {property_url}")
            
            # Salvar backup periodicamente
            if i % 25 == 0:
                self.save_data_backup(f"_parcial_{i}")
            
            # Delay entre requisições
            time.sleep(self.get_random_delay(1.5, 3.0))
    
    def save_data_backup(self, suffix=""):
        """
        Salvar backup dos dados coletados
        """
        if self.imoveis_data:
            backup_json = f'imoveis_backup{suffix}.json'
            backup_csv = f'imoveis_backup{suffix}.csv'
            
            # Salvar JSON
            with open(backup_json, 'w', encoding='utf-8') as f:
                json.dump(self.imoveis_data, f, ensure_ascii=False, indent=2)
            
            # Salvar CSV
            df = pd.DataFrame(self.imoveis_data)
            df.to_csv(backup_csv, index=False, encoding='utf-8')
            
            self.logger.info(f"Backup salvo com {len(self.imoveis_data)} imóveis: {backup_json}")
    
    def save_final_data(self):
        """
        Salvar dados finais
        """
        if not self.imoveis_data:
            self.logger.warning("Nenhum dado coletado para salvar")
            return
        
        # Salvar JSON
        with open('imoveis_teixeira_carvalho_melhorado.json', 'w', encoding='utf-8') as f:
            json.dump(self.imoveis_data, f, ensure_ascii=False, indent=2)
        
        # Preparar dados para CSV
        data_for_csv = []
        for imovel in self.imoveis_data:
            imovel_csv = imovel.copy()
            for key, value in imovel_csv.items():
                if isinstance(value, list):
                    imovel_csv[key] = '; '.join(map(str, value))
            data_for_csv.append(imovel_csv)
        
        # Salvar CSV
        df = pd.DataFrame(data_for_csv)
        df.to_csv('imoveis_teixeira_carvalho_melhorado.csv', index=False, encoding='utf-8')
        
        self.logger.info(f"Dados finais salvos: {len(self.imoveis_data)} imóveis")
        self.print_statistics()
    
    def print_statistics(self):
        """
        Imprimir estatísticas dos dados coletados
        """
        if not self.imoveis_data:
            return
        
        df = pd.DataFrame(self.imoveis_data)
        
        print("\n" + "="*60)
        print("ESTATÍSTICAS DOS DADOS COLETADOS (VERSÃO MELHORADA)")
        print("="*60)
        print(f"Total de imóveis: {len(self.imoveis_data)}")
        print(f"URLs processadas: {len(self.processed_urls)}")
        
        if 'operacao' in df.columns and not df['operacao'].empty:
            print(f"\nPor operação:")
            print(df['operacao'].value_counts())
        
        if 'tipo' in df.columns and not df['tipo'].empty:
            print(f"\nPor tipo:")
            print(df['tipo'].value_counts())
        
        if 'bairro' in df.columns and not df['bairro'].empty:
            print(f"\nTop 10 bairros:")
            print(df['bairro'].value_counts().head(10))
        
        # Qualidade dos dados
        print(f"\nQualidade dos dados:")
        print(f"- Imóveis com preço: {df['preco'].notna().sum()}")
        print(f"- Imóveis com área: {df['area_util'].notna().sum()}")
        print(f"- Imóveis com descrição: {df['descricao'].notna().sum()}")
        print(f"- Imóveis com imagens: {sum(1 for imgs in df['imagens'] if imgs)}")
        
        print("\n" + "="*60)

def main():
    """
    Função principal
    """
    scraper = TeixeiraCarvalhoScraperMelhorado()
    
    try:
        print("Iniciando scraping melhorado do site Teixeira de Carvalho...")
        scraper.scrape_all_properties()
        scraper.save_final_data()
        print("Scraping concluído com sucesso!")
        
    except KeyboardInterrupt:
        print("\nScraping interrompido pelo usuário")
        scraper.save_data_backup("_interrompido")
    except Exception as e:
        print(f"Erro durante o scraping: {e}")
        scraper.save_data_backup("_erro")

if __name__ == "__main__":
    main()