cd "`dirname "$0"`"
while read id rest; do
  if [ "$id" = "Lemma-id" ]; then
    continue
  fi
  hidden[$id]=1
done <../data/skjult_for_tagger_bm.tsv
# "kris"
hidden[37785]=1

# Exceptions (i.e. words from skjult_for_tagger_bm that shouldn't actually be hidden):
while read id rest; do
  hidden[$id]=0
done <../data/inn-igjen-i-ordbanken-bm.txt

while read id rest; do
  if [ "$id" = "Lemma-id" ]; then
    continue
  fi
  hidden_nn[$id]=1
done <../data/skjult_for_tagger_nn.tsv
# "kris"
hidden_nn[51007]=1

# Exceptions (i.e. words from skjult_for_tagger_nn that shouldn't actually be hidden):
while read id rest; do
  hidden_nn[$id]=0
done <../data/inn-igjen-i-ordbanken-nn.txt
