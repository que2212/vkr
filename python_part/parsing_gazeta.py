import time
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from rt_parsing import df_articles_base


def get_gazeta_links_with_dates(query: str, date_from: str, date_to: str, save_path: str = "gazeta_links.csv") -> pd.DataFrame:
    base_url = "https://www.gazeta.ru"
    search_url = (
        f"https://www.gazeta.ru/search.shtml?p=main&page=1&text={query}&input=utf8"
        f"&from={date_from}&to={date_to}&sort_order=published_desc"
    )

    options = Options()
    # options.add_argument('--headless')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    links = []
    dates = []
    seen_links = set()

    try:
        driver.get(search_url)
        wait = WebDriverWait(driver, 10)

        while True:
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            results = soup.select("div.b_ear-title > a")
            times = soup.select("time.b_ear-time")

            for link_el, time_el in zip(results, times):
                href = link_el.get("href")
                if not href:
                    continue

                full_link = urljoin(base_url, href)

                if full_link in seen_links:
                    continue

                seen_links.add(full_link)
                links.append(full_link)

                date_raw = time_el.get("datetime") or time_el.text.strip()
                try:
                    parsed_date = datetime.strptime(date_raw[:10], "%Y-%m-%d")
                except:
                    try:
                        parsed_date = datetime.strptime(date_raw.strip().split(',')[0], "%d.%m.%Y")
                    except:
                        parsed_date = None

                if parsed_date:
                    dates.append(parsed_date.strftime("%Y-%m-%d"))
                    if parsed_date <= datetime.strptime("2016-12-31", "%Y-%m-%d"):
                        print("Достигнута нижняя граница по дате.")
                        df = pd.DataFrame({"link": links, "date": dates})
                        df.to_csv(save_path, index=False)
                        print(f"Сохранено в {save_path}")
                        return df
                else:
                    dates.append("")

            try:
                show_more_btn = wait.until(EC.presence_of_element_located((By.ID, "_id_showmorebtn_link")))
                text = show_more_btn.text.strip().lower()

                if "по вашему запросу больше ничего не найдено" in text:
                    print("Сообщение: По вашему запросу больше ничего не найдено.")
                    break

                if not show_more_btn.is_displayed():
                    print("Кнопка 'Показать ещё' больше не отображается.")
                    break

                driver.execute_script("arguments[0].scrollIntoView(true);", show_more_btn)
                time.sleep(1)
                show_more_btn.click()

            except Exception:
                print("Кнопка 'Показать ещё' не найдена или больше неактивна.")
                break

        df = pd.DataFrame({"link": links, "date": dates})
        df.to_csv(save_path, index=False)
        print(f"Сохранено в {save_path}")
        return df

    finally:
        driver.quit()



def fetch_gazeta_article_info(df_links: pd.DataFrame) -> pd.DataFrame:
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # можно включить для ускорения
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
    text_lengths = []

    for i, link in enumerate(df_links['link'], start=1):
        try:
            print(f"[{i}] Открываем {link}")
            driver.get(link)
            time.sleep(2)

            # Заголовок
            try:
                try:
                    title_el = driver.find_element(By.CSS_SELECTOR, "div.b_article-title > h1")
                except:
                    title_el = driver.find_element(By.CSS_SELECTOR, "#_id_article > div.b_article-header > h1")
                title = title_el.text.strip()
            except:
                title = ''

            # Подзаголовок
            try:
                try:
                    subtitle_el = driver.find_element(By.CSS_SELECTOR, "div.b_article-title > div")
                except:
                    subtitle_el = driver.find_element(By.CSS_SELECTOR, "#_id_article > div.b_article-header > div.subheader")
                subtitle = subtitle_el.text.strip()
            except:
                subtitle = ''

            # Саммари
            try:
                summary_el = driver.find_element(By.CSS_SELECTOR, "div.b_article-intro > span")
                summary = summary_el.text.strip()
            except:
                summary = ''

            # Текст статьи
            try:
                paragraphs = driver.find_elements(By.CSS_SELECTOR, "#_id_article > div > p")
                text = '\n'.join(p.text.strip() for p in paragraphs if p.text.strip())
            except:
                text = ''

            # Дата публикации
            try:
                date_el = driver.find_element(By.CSS_SELECTOR, "div.breadcrumb > time")
                publication_date = date_el.get_attribute("datetime") or date_el.text.strip()
            except:
                publication_date = ''

            length = len(text)

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
            text_lengths.append(length)

        except Exception as e:
            print(f"[{i}] Ошибка при получении данных статьи: {e}")
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

    print("Парсинг завершён. Возвращается датафрейм с формой:", df_links.shape)
    print(df_links[['link', 'title', 'text_length']].head())

    return df_links


df = get_gazeta_links_with_dates(
    query='трудовые мигранты',
    date_from='2016-12-31',
    date_to='2025-05-21',
    save_path='gazeta_migrants_links.csv'
)

print(df.head())  # Показываем первые строки
print(f'Всего ссылок собрано: {len(df)}')


df_articles_base = fetch_gazeta_article_info(df)


df_articles_base.to_csv('gazeta_base.csv', index=False)
