import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import re
import matplotlib.pyplot as plt

# Путь к локальной папке с моделью и токенизатором
local_model_path = ##########

# Загружаем модель и токенизатор из локальной папки
tokenizer = AutoTokenizer.from_pretrained(local_model_path)
model = AutoModelForSequenceClassification.from_pretrained(local_model_path)

# Функция для получения сентимента (1-5 звёзд)
def get_sentiment_score(text):
    if not isinstance(text, str) or text.strip() == "":
        return np.nan
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    scores = outputs.logits.softmax(dim=1).cpu().numpy()[0]
    rating = np.dot(np.arange(1, 6), scores)
    return rating

# Функция для извлечения контекста вокруг "мигрант"
def extract_context(text, keyword="мигрант", window=5):
    if not isinstance(text, str):
        return []
    tokens = re.findall(r'\b\w+\b', text.lower())
    contexts = []
    for i, token in enumerate(tokens):
        if keyword in token:
            start = max(0, i - window)
            end = min(len(tokens), i + window + 1)
            context = ' '.join(tokens[start:end])
            contexts.append(context)
    return contexts

# Подсчёт сентимента по контекстам, усреднение
def sentiment_of_contexts(contexts):
    if not contexts:
        return np.nan
    scores = [get_sentiment_score(text) for text in contexts]
    scores = [s for s in scores if not np.isnan(s)]
    if len(scores) == 0:
        return np.nan
    return np.mean(scores)

# Загрузка данных
df = pd.read_csv('final_whole.csv')
df = df.dropna(subset=['article_text', 'date'])
df['year'] = df['date'].astype(int)
df = df[(df['year'] >= 2017) & (df['year'] <= 2025)]

# Применяем анализ
df['contexts'] = df['article_text'].apply(lambda x: extract_context(x, keyword="мигрант"))
df['sentiment'] = df['contexts'].apply(sentiment_of_contexts)

# Средний сентимент по годам
sent_by_year = df.groupby('year')['sentiment'].mean().reset_index()

# Визуализация
plt.figure(figsize=(12, 7))
plt.plot(sent_by_year['year'], sent_by_year['sentiment'], marker='o', linestyle='-', color='purple')
plt.xlabel('Год', fontsize=14)
plt.ylabel('Средний рейтинг сентимента (1-5)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.5)
plt.xticks(sent_by_year['year'], rotation=45)
plt.tight_layout()
plt.savefig("sentiment_transformer_by_year.png", dpi=300)
plt.show()
