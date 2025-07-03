library(tidyverse)
library(udpipe)
library(here)

df_whole <- read.csv(here('data', 'final_whole.csv'))

udpipe_x <- udpipe(df_whole$title, "russian")


udpipe_x$lemma <-   str_to_lower(udpipe_x$lemma)
udpipe_x <- udpipe_x %>% filter(lemma != 'год')

#создаем ДТМ из чистого юдпайпа (можно его почистить)
count_udpipe <- subset(udpipe_x, xpos %in% c("NN", "NNP", "NNS", "JJ", "JJL") | lemma %in% "казак")
count_udpipe <- count_udpipe %>% group_by(doc_id, lemma) %>% count(lemma)
library(tidytext)
corp_kazak_dtm <- count_udpipe %>% 
  cast_dtm(doc_id, term = lemma, value = n)
corp_kazak_dtm 
library(topicmodels)

#оценка модели
n_topics <- c(2, 3, 4, 5, 8, 16, 20)
text_lda_compare <- n_topics %>%
  map(LDA, x = corp_kazak_dtm, 
      control = list(seed = 1101))
data_frame(k = n_topics,
           perplex = map_dbl(text_lda_compare, perplexity)) %>%
  ggplot(aes(k, perplex)) +
  geom_point() +
  geom_line() +
  labs(title = "Оценка LDA модели",
       subtitle = "Оптимальное количество топиков",
       x = "Число топиков",
       y = "Perplexity")

#beta
kazak_lda <- LDA(corp_kazak_dtm, k = 9, control = list(seed = 1101))
kazak_topics <- tidy(kazak_lda, matrix = "beta")

#топ казак
kazak_top_terms <- kazak_topics %>% 
  group_by(topic) %>% 
  arrange(-beta) %>% 
  slice_head(n = 14) %>% 
  ungroup()

head(kazak_top_terms)
#график беты
kazak_top_terms %>% 
  mutate(term = reorder(term, beta)) %>% 
  ggplot(aes(term, beta, fill = factor(topic))) +
  geom_col(show.legend = FALSE) + 
  facet_wrap(~ topic, scales = "free", ncol=3
  ) +  coord_flip()


text_documents <- tidy(kazak_lda, matrix = "gamma")

long_posts <- udpipe_x %>%
  group_by(doc_id) %>% 
  summarise(nwords = n()) %>% 
  arrange(-nwords) %>% 
  slice_head(n = 10) %>% 
  pull(doc_id)
long_posts

text_documents %>% 
  filter(topic == 2) %>% 
  arrange(-gamma)

text_documents %>% 
  filter(document %in% long_posts) %>% 
  arrange(-gamma) %>% 
  ggplot(aes(as.factor(topic), gamma, color = document)) + 
  geom_boxplot(show.legend = F) +
  facet_wrap(~document)

#бета - для слов, гамма - для текстов





# cool visualization ------------------------------------------------------

library(ggplot2)
library(dplyr)

# Новый вектор заголовков для тем
topic_labels <- c(
  "1" = "Тема 1: Москва",
  "2" = "Тема 2: Пандемия",
  "3" = "Тема 3: Дети мигрантов и образование",
  "4" = "Тема 4: Нейтральная",
  '5' = 'Тема 5: Террористическая',
  '6' = 'Тема 6: Экономическая',
  '7' = 'Тема 7: Украинская',
  '8' = 'Тема 8: МВД и миграция',
  '9' = 'Тема 9: Трудовые отношения'
)

# Построение графика
p <- kazak_top_terms %>% 
  mutate(term = reorder(term, beta)) %>% 
  ggplot(aes(term, beta, fill = factor(topic))) +
  geom_col(show.legend = FALSE) + 
  facet_wrap(
    ~ topic,
    scales = "free",
    ncol = 3,
    labeller = as_labeller(topic_labels)
  ) +
  coord_flip() +
  theme_bw(base_size = 14) +  # увеличивает базовый размер текста
  labs(
    x = "Термин",
    y = "Вес (β)",
  )

# Сохранение в HD (например, 300 dpi)
ggsave("migrant_topics_hd.png", plot = p, width = 14, height = 8, dpi = 300)

