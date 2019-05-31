#!/bin/bash
export LC_ALL=C
cd "`dirname "$0"`"
for spraak in bm nn; do
  if [ "$spraak" = "bm" ]; then
    infile=../data/NOB-V_Leddanalyse_Vanlig.txt.xz
  else
    infile=../data/NNY-V_Leddanalyse_Vanleg.txt.xz
  fi
  outfile=../compounds_${spraak}.py
  /bin/echo -n >$outfile
  echo "compoundHash = {" >>$outfile
  xzcat $infile |awk -F'\t' '{print $2}' |\
    ruby -Ku -lne 'puts "    \"#{$_.gsub("*", "")}\": [#{$_.count("*-") + 1}],"' |\
    sort -u >>$outfile
  echo "}" >>$outfile
done
