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
  echo "# vim: set fileencoding=utf-8 :" >>$outfile
  echo "from __future__ import unicode_literals" >>$outfile
  echo "compoundHash = {" >>$outfile
  xzcat $infile | ruby -Ku -F"\t" -lane '
    next if $F[1] == ""
    puts %Q{    "#{$F[1].gsub("*", "")}": [#{$F[1].count("*-") + 1}, "#{$F[4].gsub(/-$/, "")}", "#{$F[6]}", "#{$F[2]}"],}' |\
    sort -u >>$outfile
  echo "}" >>$outfile
done
