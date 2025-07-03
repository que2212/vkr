library(tidyverse)
library(rvest)
library(readxl)
library(xlsx)
library(ggthemes)
library(ggsci)
library(ggrepel)
library(here)
library(udpipe)

udpipe_x <- udpipe(data$article_text, "russian")


# k-yadra -----------------------------------------------------------------



x <- udpipe_x %>%
  filter(upos=="NOUN") %>% 
  group_by(lemma) %>% 
  add_count() %>% 
  filter(n > 100)# %>% 
  #select(-n)

cooc <- cooccurrence(x, term = "lemma", group = "sentence_id")
cooc <- cooc %>% 
  as_tibble() %>% 
  slice_head(n = 200) %>% 
  rename(value = cooc)
cooc
library(igraph)
confessions_graph <- graph_from_data_frame(cooc, directed = F)
confessions_graph

#ЦЕНТРАЛЬНОСТЬ
{
  degrees <- degree(confessions_graph)
  sort(degrees, decreasing = T)[1:10]
  
  closeness <- closeness(confessions_graph)
  sort(closeness, decreasing = T)[1:10]
  
  membership <- components(confessions_graph)$membership
  table(membership)
  
  confessions_subgraph = induced_subgraph(confessions_graph, 
                                          which(membership == 1))
  closeness <- closeness(confessions_subgraph)
  sort(closeness, decreasing = T)[1:10]
  
  names(centralization.closeness(confessions_graph))
  centralization.closeness(confessions_graph)$centralization
  
  betweenness <- betweenness(confessions_graph)
  sort(betweenness, decreasing = T)[1:10]
  
  names(centralization.closeness(confessions_graph))
  
  centralization.closeness(confessions_graph)$centralization
}

#точки связности
{
  articulation_points(confessions_graph)
  
  clique_num(confessions_graph)
  cliques(confessions_graph, min=3)
  
  largest_cliques(confessions_graph)
}

#К-ядро
{
  coreness <- coreness(confessions_graph)
  head(coreness)
  table(coreness)
  #визуал К-ядер
  names(get.vertex.attribute(confessions_graph))
  V(confessions_graph)$color <- coreness
  names(get.vertex.attribute(confessions_graph))
}
library(ggraph)

png(width = 1920, height = 1080)
ggraph(confessions_graph, layout = "fr") + 
  geom_edge_link(edge_alpha = 0.2) +
  geom_node_point(aes(fill = as.factor(color)),
                  color= "grey30", 
                  size = log2(degrees) * 4, 
                  alpha = 0.5, 
                  shape = 21) + 
  geom_node_text(aes(label = name), vjust = 1, hjust = 1, check_overlap = F,  size = 5.5)+
  theme(
    text = element_text(size = 18)
  )#+ 
#theme_void()
ggsave("kyadr.png")        
dev.off()


confessions2_3 <- induced_subgraph(confessions_graph, vids=which(coreness == 10 |
                                                                   coreness == 1 |
                                                                   coreness == 2))

ggraph(confessions2_3, layout = "fr") + 
  geom_edge_link(edge_alpha = 0.2) +
  geom_node_point(aes(fill = as.factor(color)),
                  color= "grey30", 
                  size = 4,
                  alpha = 0.5, 
                  shape = 21) + 
  geom_node_text(aes(label = name), vjust = 1, hjust = 1) + 
  theme_void()
