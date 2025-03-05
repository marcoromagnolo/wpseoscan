#!/bin/bash

# Enable Python Virtual Env and Activate
python3 -m venv .venv
source ./.venv/bin/activate

# Install Python packages
pip install -r requirements.txt
python3 -m spacy download it_core_news_sm
#python3 -m spacy download it_core_news_md
#python3 -m spacy download it_core_news_lg
python3 -m pip install --upgrade nltk
python -m nltk.downloader omw-1.4
python -m nltk.downloader wordnet

# Create dirs
mkdir log
