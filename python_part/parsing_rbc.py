import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_rbc_links_by_date_range(query: str, date_from: str, date_to: str, save_path: str = "rbc_links.csv") -> pd.DataFrame:
    query_encoded = query.replace(' ', '%20')
    search_url = (
        f'https://www.rbc.ru/search/?query={query_encoded}'
        f'&dateFrom={date_from}&dateTo={date_to}'
    )
    base_url = 'https://www.rbc.ru'

    options = Options()
    # options.add_argument('--headless')  # включи при необходимости
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(search_url)
        time.sleep(4)

        collected = set()
        links = []
        dates = []

        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            articles = soup.select('div.js-search-container > div')

            added = False

            for article in articles:
                a_tag = article.select_one('a')
                date_tag = article.select_one('span')

                if not a_tag or not date_tag:
                    continue

                href = a_tag.get('href')
                raw_text = date_tag.text.strip()

                # Извлекаем дату (например, "16 дек 2024" или "22 мая")
                match = re.search(r'(\d{1,2} \w+)(?: (\d{4}))?', raw_text)
                if match:
                    day_month = match.group(1)
                    year = match.group(2) if match.group(2) else '2025'
                    date_text = f"{day_month} {year}"
                else:
                    date_text = ''

                if href and href not in collected:
                    collected.add(href)
                    full_link = urljoin(base_url, href)
                    links.append(full_link)
                    dates.append(date_text)
                    added = True

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Больше нечего загружать. Сохраняем результат.")
                break
            last_height = new_height

        df = pd.DataFrame({'link': links, 'date': dates})
        df.to_csv(save_path, index=False)
        print(f"Сохранено в {save_path}")
        return df

    finally:
        driver.quit()


def fetch_article_info(df_links: pd.DataFrame) -> pd.DataFrame:
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Включи при необходимости
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    titles, subtitles, summaries, article_texts = [], [], [], []
    publication_dates, text_lengths = [], []

    for i, link in enumerate(df_links['link'], start=1):
        try:
            print(f"[{i}] Открываем {link}")
            driver.get(link)
            time.sleep(2)

            # Заголовок
            try:
                title = driver.find_element(By.CSS_SELECTOR, 'h1').text.strip()
            except:
                title = ''

            # Подзаголовок
            try:
                subtitle = driver.find_element(By.CSS_SELECTOR, 'header span').text.strip()
            except:
                subtitle = ''

            # Саммари
            try:
                summary = driver.find_element(By.CSS_SELECTOR, 'header p').text.strip()
            except:
                summary = ''

            # Основной текст
            try:
                paragraphs = driver.find_elements(By.CSS_SELECTOR, 'div.article__text, div.article-feature-item-title ~ p')
                text = '\n'.join(p.text.strip() for p in paragraphs if p.text.strip())
            except:
                text = ''

            # Дата публикации
            try:
                date_el = driver.find_element(By.CSS_SELECTOR, 'div.article-entry-update.caption-1-short')
                publication_date = date_el.text.strip()
            except:
                publication_date = ''

            length = len(text)

            print(f"[{i}] Заголовок: {title}")
            if subtitle: print(f"[{i}] Подзаголовок: {subtitle}")
            if summary: print(f"[{i}] Саммари: {summary[:60]}...")
            if publication_date: print(f"[{i}] Дата публикации: {publication_date}")
            if text: print(f"[{i}] Текст статьи: {length} символов")

            titles.append(title)
            subtitles.append(subtitle)
            summaries.append(summary)
            article_texts.append(text)
            publication_dates.append(publication_date)
            text_lengths.append(length)

        except Exception as e:
            print(f"[{i}] Ошибка: {e}")
            titles.append('')
            subtitles.append('')
            summaries.append('')
            article_texts.append('')
            publication_dates.append('')
            text_lengths.append(0)

    driver.quit()

    df_links['title'] = titles
    df_links['subtitle'] = subtitles
    df_links['summary'] = summaries
    df_links['article_text'] = article_texts
    df_links['publication_date'] = publication_dates
    df_links['text_length'] = text_lengths

    return df_links



df = get_rbc_links_by_date_range(
    query="трудовые мигранты",
    date_from="01.01.2017",
    date_to="21.05.2025",
    save_path="rbc_links.csv"
)


df_database = fetch_article_info(df)
df_database.drop_duplicates()
df_database.to_csv("rbc_database.csv", index=False)


import pandas as pd
df2 = pd.read_csv("rbc_database.csv")

df2 = df2.merge(df[['link', 'date']], on='link', how='left', suffixes=('', '_new'))
df2['date'] = df2['date_new'].combine_first(df2['date'])
df2.drop(columns='date_new', inplace=True)
df2.to_csv("rbc_database.csv", index=False)
