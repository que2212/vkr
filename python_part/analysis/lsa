import pandas as pd
import numpy as np
import re
import spacy_udpipe
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

print("=== Шаг 1: Загрузка данных ===")
df = pd.read_csv("final_whole.csv")
print(f"Исходных строк: {len(df)}")

df = df[~df["date"].astype(str).str.startswith("2016")]
print(f"Строк после удаления 2016 года: {len(df)}")

df = df.dropna(subset=["article_text", "date"])
print(f"Строк после удаления NaN: {len(df)}")

# === Шаг 2: Предобработка текста ===
print("Загружаем стоп-слова...")
nltk.download("stopwords")
stop_words = set(stopwords.words("russian"))
custom_stopwords = stop_words.union({
    'это', 'который', 'такой', 'весь', 'самый', 'один', 'другой',
    'ещё', 'уже', 'свой', 'наш', 'ваш', 'их', 'них',
    'некоторый', 'тот', 'этот', 'тоже', 'всегда', 'никогда', 'иногда',
    'теперь', 'именно', 'либо', 'каждый', 'какой', 'почему', 'потому', 'если', 'тогда'
})
print(f"Общее количество стоп-слов: {len(custom_stopwords)}")

print("Загружаем модель spaCy для русского языка...")
nlp = spacy_udpipe.load("ru")

def clean_text(text):
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower()

print("Предобработка и лемматизация текстов...")
texts = df["article_text"].astype(str).apply(clean_text).tolist()
cleaned_texts = []

for doc in tqdm(nlp.pipe(texts, batch_size=1000), total=len(texts), desc="Лемматизация"):
    lemmas = [
        token.lemma_ for token in doc
        if len(token.lemma_) > 2 and token.lemma_ not in custom_stopwords and token.pos_ in {'NOUN', 'VERB', 'ADJ'}
    ]
    cleaned_texts.append(" ".join(lemmas))

df.loc[:, "clean_text"] = cleaned_texts
df.loc[:, "date"] = df["date"].astype(str).str[:4]

# === Шаг 3: Группировка текстов по годам ===
print("Группировка текстов по годам...")
grouped = df.groupby("date")["clean_text"].apply(lambda texts: " ".join(texts)).reset_index()
print("Года в выборке:", grouped["date"].tolist())

# === Шаг 4: TF-IDF + LSA ===
print("Векторизация TF-IDF...")
vectorizer = TfidfVectorizer(max_df=0.95, min_df=2)
X_tfidf = vectorizer.fit_transform(grouped["clean_text"])
print(f"Размер TF-IDF матрицы: {X_tfidf.shape}")

print("Применение TruncatedSVD (LSA)...")
n_components = min(100, X_tfidf.shape[1] - 1)
lsa = TruncatedSVD(n_components=n_components, random_state=42)
X_lsa = lsa.fit_transform(X_tfidf)
print(f"Размерность после LSA: {X_lsa.shape}")

# === Шаг 5: Косинусное сходство ===
print("Вычисление косинусного сходства...")
similarity_matrix = cosine_similarity(X_lsa)
percent_matrix = (similarity_matrix * 100).round(0)

# === Шаг 6: Визуализация ===
print("Создание и сохранение тепловой карты...")
plt.figure(figsize=(12, 7))
ax = sns.heatmap(
    similarity_matrix,
    cmap="Greens",
    annot=percent_matrix.astype(int),
    fmt="d",
    cbar=True,
    cbar_kws={"label": "Степень совпадения (%)"}
)

cbar = ax.collections[0].colorbar
cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
cbar.set_ticklabels(["0%", "25%", "50%", "75%", "100%"])

labels = grouped["date"].tolist()
ax.set_xticklabels(labels, rotation=0, fontsize=10)
ax.set_yticklabels(labels, rotation=0, fontsize=10)

plt.xlabel("")
plt.ylabel("")
#plt.title("Косинусное сходство между годами (LSA)", fontsize=14)
plt.tight_layout()
plt.savefig("lsa_similarity_fullhd_lemmas2.png", dpi=160, bbox_inches='tight')
plt.close()
print("Готово! Файл сохранён как lsa_similarity_fullhd_lemmas2.png")
