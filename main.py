#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Principal - Scraping Imóveis Teixeira de Carvalho
======================================================

Este script realiza:
1. Scraping completo do site da Teixeira de Carvalho
2. Extração de dados de todos os imóveis
3. Salvamento em formatos JSON e CSV
4. Geração de dashboard HTML com análises

Autor: AI Assistant
Data: 2025
"""

import os
import sys
import time
from datetime import datetime

# Importar classes customizadas
from scraper_teixeira_carvalho import TeixeiraCarvalhoScraper
from dashboard_generator import DashboardGenerator

def check_dependencies():
    """
    Verificar se todas as dependências estão instaladas
    """
    required_packages = [
        'requests', 'bs4', 'pandas', 'plotly', 'lxml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Dependências não encontradas:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Para instalar as dependências, execute:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ Todas as dependências estão instaladas")
    return True

def print_banner():
    """
    Imprimir banner do projeto
    """
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🏠 SCRAPER IMÓVEIS TEIXEIRA DE CARVALHO       ║
    ║                                                              ║
    ║  📊 Extração e Análise Completa de Dados Imobiliários       ║
    ║  🌐 Site: www.teixeiradecarvalho.com.br                     ║
    ║  📈 Dashboard com visualizações interativas                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_menu():
    """
    Mostrar menu de opções
    """
    menu = """
    🔧 OPÇÕES DISPONÍVEIS:
    
    1. 🚀 Executar Scraping Completo
    2. 📊 Gerar Dashboard (dados existentes)
    3. 🔄 Scraping + Dashboard (processo completo)
    4. 📋 Verificar Status dos Arquivos
    5. ❌ Sair
    
    """
    print(menu)

def check_files_status():
    """
    Verificar status dos arquivos de dados
    """
    files_to_check = [
        'imoveis_teixeira_carvalho.json',
        'imoveis_teixeira_carvalho.csv',
        'dashboard_imoveis.html',
        'scraper_log.log'
    ]
    
    print("\n📁 STATUS DOS ARQUIVOS:")
    print("="*50)
    
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            modified = datetime.fromtimestamp(os.path.getmtime(file))
            print(f"✅ {file}")
            print(f"   📏 Tamanho: {size:,} bytes")
            print(f"   🕒 Modificado: {modified.strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            print(f"❌ {file} - Não encontrado")
        print()

def run_scraping():
    """
    Executar processo de scraping
    """
    print("\n🚀 INICIANDO SCRAPING...")
    print("="*50)
    
    start_time = time.time()
    
    try:
        scraper = TeixeiraCarvalhoScraper()
        print("📡 Conectando ao site...")
        
        scraper.scrape_all_properties()
        scraper.save_final_data()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Scraping concluído com sucesso!")
        print(f"⏱️ Tempo total: {duration:.2f} segundos")
        print(f"📊 Dados salvos em arquivos JSON e CSV")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrompido pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ Erro durante o scraping: {e}")
        return False

def run_dashboard():
    """
    Gerar dashboard
    """
    print("\n📊 GERANDO DASHBOARD...")
    print("="*50)
    
    try:
        dashboard = DashboardGenerator()
        dashboard.generate_dashboard()
        
        print("✅ Dashboard gerado com sucesso!")
        print("🌐 Abra o arquivo 'dashboard_imoveis.html' no navegador")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar dashboard: {e}")
        return False

def run_complete_process():
    """
    Executar processo completo: scraping + dashboard
    """
    print("\n🔄 EXECUTANDO PROCESSO COMPLETO...")
    print("="*60)
    
    # Fase 1: Scraping
    print("\n📡 FASE 1: SCRAPING DE DADOS")
    if not run_scraping():
        print("❌ Falha no scraping. Processo interrompido.")
        return False
    
    print("\n⏳ Aguardando 3 segundos...")
    time.sleep(3)
    
    # Fase 2: Dashboard
    print("\n📊 FASE 2: GERAÇÃO DE DASHBOARD")
    if not run_dashboard():
        print("❌ Falha na geração do dashboard.")
        return False
    
    print("\n🎉 PROCESSO COMPLETO FINALIZADO COM SUCESSO!")
    print("📁 Arquivos gerados:")
    print("   - imoveis_teixeira_carvalho.json")
    print("   - imoveis_teixeira_carvalho.csv")
    print("   - dashboard_imoveis.html")
    
    return True

def main():
    """
    Função principal
    """
    print_banner()
    
    # Verificar dependências
    if not check_dependencies():
        print("\n❌ Execute a instalação das dependências antes de continuar.")
        sys.exit(1)
    
    while True:
        show_menu()
        
        try:
            choice = input("Escolha uma opção (1-5): ").strip()
            
            if choice == '1':
                run_scraping()
                
            elif choice == '2':
                run_dashboard()
                
            elif choice == '3':
                run_complete_process()
                
            elif choice == '4':
                check_files_status()
                
            elif choice == '5':
                print("\n👋 Finalizando o programa...")
                break
                
            else:
                print("❌ Opção inválida. Escolha entre 1-5.")
            
            input("\n⏸️ Pressione Enter para continuar...")
            os.system('clear' if os.name == 'posix' else 'cls')  # Limpar tela
            
        except KeyboardInterrupt:
            print("\n\n👋 Programa interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            input("⏸️ Pressione Enter para continuar...")

if __name__ == "__main__":
    main()