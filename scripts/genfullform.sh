#!/bin/bash

cd "`dirname "$0"`"
. ./skjult_for_tagger.sh

for spraak in bm nn; do
previous_fullform=
previous_lemma_features=
{
  echo "# vim: set fileencoding=utf-8 :"
  echo "from __future__ import unicode_literals"
} >../fullform_${spraak}.py
{
  echo "fullformHash = {"
  xzcat ../data/fullform_${spraak}.txt.xz |iconv -f iso-8859-1 -t utf-8 |grep -v '^*' |\
      #LC_ALL=C sort -n -t: -k3,3 |\
      LC_ALL=C sort -t'	' -k3,3 -s |\
      awk -F'\t' '{print $1":"$3":\""$2"\" "$4}' |while IFS=: read id fullform lemma_features; do
    case $id in
      ''|*[!0-9]*) false ;;
      *) if [ "$spraak" = "bm" -a "${hidden[$id]}" = "1" ] || [ "$spraak" = "nn" -a "${hidden_nn[$id]}" = "1" ] ; then
           continue
         fi
         ;;
    esac
    if [ "$fullform" = "" ]; then
      continue
    fi
    if [ "$fullform" = "$previous_fullform" ]; then
      if [ "$lemma_features" != "$previous_lemma_features" ]; then
        echo -e "\t${lemma_features//\'/\'}";
      fi
    else
      [ -z "$previous_fullform" ] || echo "',"
      echo "    '"${fullform//\'/\\\'}"': '"${lemma_features//\'/\\\'}
      previous_fullform="$fullform"
    fi
    previous_lemma_features="$lemma_features"
  done
  echo -e "'}"
} |ruby -ne 'print $_.gsub("\n", "\\n").
                      gsub("'\'',\\n", "'\'',\n").
                      gsub("{\\n", "{\n").
                      gsub("'\''}\\n", "'\''\n}\n").
                      gsub("\t", "\\t")' >>../fullform_${spraak}.py
done
