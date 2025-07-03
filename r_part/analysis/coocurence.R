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


cooccur <- cooccurrence(udpipe_x$lemma,
                        relevant = udpipe_x$upos %in% c("NOUN", 
                                                        "VERB", "ADJ"),
                        skipgram = 1)
head(cooccur)

png(width = 1280, height = 720)
wordnetwork <- head(cooccur, 100)
wordnetwork <- graph_from_data_frame(wordnetwork)
ggraph(wordnetwork, layout = "fr")+
  geom_edge_link(aes(width = cooc, edge_alpha = cooc), show.legend = FALSE,
                 edge_colour = "#ed9de9")+
  geom_node_text(aes(label = name), col = "darkblue",
                 size = 5, repel = TRUE)+
  geom_node_point(position = "jitter", color = "darkblue", size = 3)+
  theme(plot.title = element_text(size = 17),
        plot.subtitle = element_text(size = 14))
ggsave("bigram_title_all.png")        
dev.off()
