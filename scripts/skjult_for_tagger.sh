cd "`dirname "$0"`"
while read id rest; do
  if [ "$id" = "Lemma-id" ]; then
    continue
  fi
  hidden[$id]=1
done < <(grep -v 'tusenvis\|hilse' ../data/skjult_for_tagger_bm.tsv)
# "kris"
hidden[37785]=1

while read id rest; do
  if [ "$id" = "Lemma-id" ]; then
    continue
  fi
  hidden_nn[$id]=1
done < <(cat ../data/skjult_for_tagger_nn.tsv)
# "kris"
hidden_nn[51007]=1
