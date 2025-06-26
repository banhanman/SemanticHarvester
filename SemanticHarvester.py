import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import argparse
import json
import re
import sys

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def get_page_content(url):
    """Получение содержимого веб-страницы с обработкой ошибок"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {str(e)}")
        return None

def extract_text(html):
    """Извлечение текста из HTML с очисткой"""
    soup = BeautifulSoup(html, 'lxml')
    
    for element in soup(["script", "style", "meta", "link", "footer", "nav", "header"]):
        element.decompose()
    
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def analyze_keywords(text, lang='english', top_n=20):
    """Анализ ключевых слов с использованием NLP"""
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalnum() and len(word) > 2]
    
    stop_words = set(stopwords.words(lang))
    filtered_words = [word for word in words if word not in stop_words]
    
    word_freq = Counter(filtered_words)
    return word_freq.most_common(top_n)

def detect_language(text):
    """Простое определение языка по преобладающим символам"""
    if re.search(r'[а-яё]', text, re.IGNORECASE):
        return 'russian'
    return 'english'

def process_site(url):
    """Обработка одного сайта"""
    print(f"\n[🔍] Анализ: {url}")
    html = get_page_content(url)
    if not html:
        return None
    
    text = extract_text(html)
    if not text.strip():
        print(f"[⚠] Предупреждение: Не удалось извлечь текст из {url}")
        return None
    
    lang = detect_language(text)
    keywords = analyze_keywords(text, lang)
    
    return {
        'url': url,
        'language': lang,
        'keywords': keywords,
        'text_sample': text[:500] + "..."  # Сохраняем образец текста
    }

def save_results(results, output_file):
    """Сохранение результатов в JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[💾] Результаты сохранены в {output_file}")

def main():
    parser = argparse.ArgumentParser(description='SemanticHarvester - Сбор семантики сайтов')
    parser.add_argument('sites', nargs='+', help='URL сайтов для анализа')
    parser.add_argument('-o', '--output', default='semantic_results.json', help='Выходной файл (по умолчанию: semantic_results.json)')
    
    args = parser.parse_args()
    
    if not args.sites:
        print("Ошибка: Не указаны URL сайтов")
        sys.exit(1)
    
    results = []
    for url in args.sites:
        result = process_site(url)
        if result:
            results.append(result)
            print(f"[✅] Найдено ключевых слов: {len(result['keywords'])}")
            print("    Топ-5 ключевых слов:")
            for word, freq in result['keywords'][:5]:
                print(f"    - {word}: {freq}")
    
    if results:
        save_results(results, args.output)
    else:
        print("[❌] Не удалось получить данные ни с одного сайта")

if __name__ == "__main__":
    main()
