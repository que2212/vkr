import pandas as pd
import numpy as np

#### gazeta
df_gazeta = pd.read_csv('gazeta_base.csv')
df_gazeta.publication_date = df_gazeta.publication_date.str[:4]
df_gazeta.date = df_gazeta.publication_date
df_gazeta.drop('publication_date', axis=1, inplace=True)
df_gazeta.to_csv('final_gazeta.csv', index=False)

#### rbc
df_rbc = pd.read_csv('rbc_database.csv')


# Ключевые слова
keywords = ["рус", "росс", "мвд", "рф"]

# Корни субъектов РФ
subject_roots = [
    "москов", "санкт-петербург", "ленинград", "севастополь", "республика алтай", "алтайск", "амур", "архангел",
    "астрахан", "башк", "белгород", "брян", "бурят", "владимир", "волгоград", "вологод", "воронеж", "еврей",
    "забайкал", "иванов", "ингуш", "иркут", "кабарди", "калининград", "калмык", "калуж", "камчат", "карач", "карел",
    "кемеров", "киров", "коми", "костром", "краснодар", "краснояр", "курган", "курск", "ленинск", "липецк", "магадан",
    "марий", "морд", "мурман", "ненец", "нижегород", "новгород", "новосибир", "омск", "оренбург", "орлов", "осет",
    "пенз", "перм", "примор", "псков", "адыг", "алтай", "ростов", "рязан", "самар", "саратов", "саха", "сахалин",
    "свердлов", "смолен", "ставропол", "тамбов", "татарстан", "твер", "томск", "туль", "тюмен", "удмурт", "ульянов",
    "хабаров", "ханты", "челябин", "чечен", "чуваш", "чукот", "ямало", "ярослав"
]

# Объединяем ключи и корни
all_keywords = keywords + subject_roots

# Временный столбец с пониженным регистром
lowered = df_rbc['article_text'].str.lower()
lowered = df_rbc['article_text'].fillna('').astype(str).str.lower()
# Создаём маску: True, если хотя бы одно ключевое слово найдено
mask = lowered.apply(lambda text: any(kw in text for kw in all_keywords))

# Применяем фильтр к оригинальному DataFrame, регистр сохраняем
df_rbc_filtered = df_rbc[mask].copy()
df_rbc_filtered.drop('publication_date', axis=1, inplace=True)
df_rbc_filtered.date = df_rbc.date.str[-4:]
df_rbc_filtered.to_csv('final_rbc.csv', index=False)


### rt
df_rt = pd.read_csv('rt_database.csv')
df_rt.drop('publication_date', axis=1, inplace=True)
df_rt.date = df_rt.date.str[:4]
df_rt.to_csv('final_rt.csv', index=False)

### whole_df

df_rt['source'] = 'rt'
df_rbc_filtered['source'] = 'rbc'
df_gazeta['source'] = 'gazeta'
df_whole = pd.concat([df_gazeta, df_rbc_filtered, df_rt], ignore_index=True)
df_whole.to_csv('final_whole.csv', index=False)
