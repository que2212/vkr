from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import time
import datetime

def get_russia_links_with_dates_selenium(query: str, until_date: str = None) -> pd.DataFrame:
    base_url = 'https://russian.rt.com'
    search_url = f'{base_url}/search?q={query}'
    if until_date:
        search_url += f'&type=&df=&dt={until_date}'

    options = Options()
    #options.add_argument('--headless')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(search_url)
        time.sleep(3)

        last_count = 0
        while True:
            try:
                load_more_button = driver.find_element(By.CSS_SELECTOR, '#search-serp > div.listing.listing_all-new.listing_js > div > div > div > a')
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(1)
                load_more_button.click()
                time.sleep(3)

                current_count = len(driver.find_elements(By.CSS_SELECTOR, '#search-serp > div.listing.listing_all-new.listing_js > div > ul > li'))
                if current_count == last_count:
                    break
                last_count = current_count

            except Exception:
                break

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links_tags = soup.select('#search-serp > div.listing.listing_all-new.listing_js > div > ul > li > div > div > div.card__heading.card__heading_all-new > a')
        dates_tags = soup.select('#search-serp > div.listing.listing_all-new.listing_js > div > ul > li > div > div > div.card__date-time.card__date-time_all-new_cover > time')

        links = []
        dates = []
        count = min(len(links_tags), len(dates_tags))

        for i in range(count):
            href = links_tags[i].get('href')
            if href:
                full_link = urljoin(base_url, href)
                if '/russia/' in full_link:
                    links.append(full_link)
                    raw_date = dates_tags[i].get('datetime') or dates_tags[i].text.strip()
                    dates.append(raw_date[:10])  # оставляем только YYYY-MM-DD

        return pd.DataFrame({'link': links, 'date': dates})

    finally:
        driver.quit()


def full_rt_migrant_parser(query: str, stop_date='2016-12-31') -> pd.DataFrame:
    all_data = pd.DataFrame(columns=['link', 'date'])
    current_date = datetime.date.today().isoformat()

    while True:
        print(f"Парсинг до даты: {current_date}")
        df = get_russia_links_with_dates_selenium(query, until_date=current_date)

        if df.empty:
            print("Ничего не найдено, завершаем.")
            break

        all_data = pd.concat([all_data, df], ignore_index=True).drop_duplicates(subset='link')

        min_date = df['date'].min()
        print(f"Минимальная дата на странице: {min_date}")

        if min_date <= stop_date:
            print("Достигнута предельная дата. Завершаем парсинг.")
            break

        current_date = min_date  # без вычитания дня, как ты просил

    return all_data.reset_index(drop=True)


def fetch_article_info(df_links):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    titles = []
    subtitles = []
    summaries = []
    article_texts = []
    publication_dates = []
    text_lengths = []  # Добавляем сюда длину текста

    for i, link in enumerate(df_links['link'], start=1):
        try:
            print(f"[{i}] Открываем {link}")
            driver.get(link)
            time.sleep(2)

            title_el = driver.find_element(By.CSS_SELECTOR, "h1.article__heading.article__heading_article-page")
            title = title_el.text.strip()

            try:
                subtitle_el = driver.find_element(By.CSS_SELECTOR, "h2.article__subtitle")
                subtitle = subtitle_el.text.strip()
            except:
                subtitle = ''

            try:
                summary_el = driver.find_element(By.CSS_SELECTOR, "div.article__summary.article__summary_article-page.js-mediator-article")
                summary = summary_el.text.strip()
            except:
                summary = ''

            try:
                paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.article__text.article__text_article-page.js-mediator-article p")
                text = '\n'.join(p.text.strip() for p in paragraphs if p.text.strip())
            except:
                text = ''

            try:
                time_el = driver.find_element(By.CSS_SELECTOR, "time.date")
                publication_date = time_el.get_attribute("datetime")
            except:
                publication_date = ''

            length = len(text)  # считаем количество символов в тексте

            print(f"[{i}] Заголовок: {title}")
            if subtitle:
                print(f"[{i}] Подзаголовок: {subtitle}")
            if summary:
                print(f"[{i}] Саммари: {summary[:60]}...")
            if publication_date:
                print(f"[{i}] Дата публикации: {publication_date}")
            if text:
                print(f"[{i}] Текст статьи: {length} символов")

            titles.append(title)
            subtitles.append(subtitle)
            summaries.append(summary)
            article_texts.append(text)
            publication_dates.append(publication_date)
            text_lengths.append(length)  # добавляем в список

        except Exception as e:
            print(f"[{i}] Ошибка при получении данных статьи: {e}")
            titles.append('')
            subtitles.append('')
            summaries.append('')
            article_texts.append('')
            publication_dates.append('')
            text_lengths.append(0)  # если ошибка, длина 0

    driver.quit()

    df_links['title'] = titles
    df_links['subtitle'] = subtitles
    df_links['summary'] = summaries
    df_links['article_text'] = article_texts
    df_links['publication_date'] = publication_dates
    df_links['text_length'] = text_lengths  # добавляем колонку с длиной текста
    return df_links



# Пример использования:
df_all = full_rt_migrant_parser('мигранты')
print(df_all)

df_all = df_all.drop_duplicates(subset='link').reset_index(drop=True)
df_all.to_csv('rt_migrants_links.csv', index=False)

df_all = pd.read_csv('rt_migrants_links.csv')

df_articles_base = fetch_article_info(df_all)
df_articles_base.drop_duplicates(subset='link', inplace=True)
df_articles_base.to_csv('rt_database.csv', index=False)
#потом проверить на дубликаты
