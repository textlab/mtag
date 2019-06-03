#!/bin/bash
export LC_ALL=C

cd "`dirname "$0"`"
. ./skjult_for_tagger.sh

for spraak in bm nn; do
{
  echo "# vim: set fileencoding=utf-8 :"
  echo "from __future__ import unicode_literals"
  echo "rootHash = {"
  xzcat ../data/fullform_${spraak}.txt.xz |iconv -f iso-8859-1 -t utf-8 |grep -v '^*' |\
  awk -F'\t' '{print $1":"$2; if ($4~"^adj.* (nøyt|komp|sup)") print $1":"$3;}' |while IFS=: read id lemma; do
    case $id in
      ''|*[!0-9]*) false ;;
      *) if [ "$spraak" = "bm" -a "${hidden[$id]}" = "1" ] || [ "$spraak" = "nn" -a "${hidden_nn[$id]}" = "1" ] ; then
           continue
         fi
         ;;
    esac
    echo "$lemma"
  done |sort -u |sed 's/-$//; s/^/    "/; s/$/": [1],/; s/\$/\\$/g'
  if [ "$spraak" = "bm" ]; then
  cat <<EOF
    "ei": [1],
    "et": [1],
    "én": [1],
    "éi": [1],
    "ett": [1],
    "étt": [1],
EOF
  fi
  echo -e "}"
} >../root_${spraak}.py
done
