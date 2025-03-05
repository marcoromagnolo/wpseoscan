from bs4 import BeautifulSoup

# Pulizia del testo HTML
def clean_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()