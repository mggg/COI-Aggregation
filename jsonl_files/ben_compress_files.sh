#!/bin/bash


for file in ./*
do
    if [ -f "$file" ]; then
        if [[ $file == *.jsonl ]]; then
            ben -m x-encode $file && rm $file &
        fi
    fi
done
