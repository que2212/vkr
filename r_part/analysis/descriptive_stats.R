
# libs --------------------------------------------------------------------

library(tidyverse)
library(here)
library(xlsx)
library(readxl)
library(MESS)
library(rstatix)
library(ggrepel)
library(ggsci)
library(openxlsx)
library(ggrain)
library(ggpubr)
library(haven)
library(labelled)


# import ------------------------------------------------------------------

data <- read.csv(here('data', 'final_whole.csv'))
data$date <- as.factor(data$date)

data <- data %>%  filter(date != 2016)

# data wrangling ----------------------------------------------------------


df <- data |> group_by(source) |> #year
  count(date) |> # частотный анализ
  mutate(pct = round_percent(n, 2),
         cum_pct = cumsum(pct)) |> ungroup() |>  na.omit()


# visualisation -----------------------------------------------------------


png(width = 1920, height = 1080)
ggplot(df) +
  geom_col(
    aes(x = date, y = n, fill = source),
    color = 'black',
    width = 0.8,
    position = position_dodge(width = 0.8)
  ) +
  geom_text(
    aes(x = date, y = n, label = n, group = source),
    position = position_dodge(width = 0.8),
    vjust = -0.3,
    size = 7,
    color = "black"
  ) +
  labs(
    x = "Год",
    y = "Количество статей"
  ) +
  theme_minimal(base_size = 20) +
  theme(
    text = element_text(size = 25),
    axis.text.x = element_text(size = 16),
    axis.text.y = element_text(size = 20),
    legend.text = element_text(size = 28)
  )+
  labs(
    fill = 'Источник'
  )+
  scale_fill_manual(values = c('#b11116', '#8cd9b8', '#77bc1f' ))
ggsave("descriptive_stats_original.png")
dev.off()
