library(tidyverse)
library(rvest)
library(readxl)
library(xlsx)
library(ggthemes)
library(ggsci)
library(ggrepel)
library(here)

library(udpipe)
library(igraph)
library(ggraph)


# bag of words ------------------------------------------------------------


pattern_data <- udpipe_x |> filter((lemma == "незаконный") |
                                     (lemma == "проверка") |
                                     (lemma == "контроль") |
                                     (lemma == "дело") |
                                     (lemma == "теракт") |
                                     (lemma == "фиктивный") |
                                     (lemma == "СК") |
                                     (lemma == "задержать") |
                                     (lemma == "борьба") |
                                     (lemma == "арестовать")) |> 
  count(lemma, sort = TRUE)


png(width = 1280, height = 720)
udpipe_x |> filter(upos == "ADJ" | upos == "VERB" | upos == "NOUN" |
                     lemma == "СК"
                   ) |> 
  filter(lemma != 'мочь' & lemma != 'быть' & lemma != 'стать' & lemma != 'мигрант' &
           lemma != 'год'
         ) %>% 
  count(lemma, sort = TRUE) |>
  slice_head(n = 23) |> 
  ggplot(aes(reorder(lemma, n), n))+
  geom_col(show.legend = FALSE, fill = "lightblue")+
  coord_flip()+
  #scale_y_continuous(breaks = seq(0, 15, by = 5))+
  labs(
    x = "Слова",
    y = "Частота"
    #title = "Наиболее часто встречающиеся слова в заголовках новостных статей про мигрантов",
    #subtitle = "22.03.24 – 30.04.24",
    #caption = "Источник: новостной портал RT"
  )+
  theme_gdocs()+
  theme(plot.title = element_text(size = 17),
        plot.subtitle = element_text(size = 14),
        axis.title = element_text(face = "bold"))
  #geom_col(data = pattern_data, aes(lemma, n), fill = "red", width = 0.9)+
  #geom_text_repel(data = pattern_data, aes(label = lemma), 
                  #min.segment.length = 0, 
                  #box.padding = 0.1, direction = "x", 
                  #nudge_y = 0.1)
ggsave("bagofwords_title.png")        
dev.off()
