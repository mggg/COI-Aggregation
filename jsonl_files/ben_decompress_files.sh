#!/bin/bash


for file in ./*
do
    if [ -f "$file" ]; then
        if [[ $file == *.xben ]]; then
            # ben -m x-decode $file && rm $file &
            ben -m x-decode $file &
        fi
    fi
done