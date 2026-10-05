#!/bin/sh
# Grades A01 and A02 N times each with grader.py; prints how often each gets PASS.
P=${PY:-python}; N=${1:-20}; cd "$(dirname "$0")"
for a in A01 A02; do
  grep "\"attack\": \"$a\"" attacks.jsonl > rt_$a.jsonl
  c=0; i=0; while [ $i -lt $N ]; do $P ../../grader.py all_tasks.jsonl rt_$a.jsonl | grep -q "^PASS" && c=$((c+1)); i=$((i+1)); done
  echo "$a: PASS $c/$N"
done
