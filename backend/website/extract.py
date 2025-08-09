import requests
from bs4 import BeautifulSoup


# 🌐 Extracts clean, readable text content from a web page (URL)
def extract_text_from_url(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Remove script and style
    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text(separator="\n")

    # Clean empty lines/whitespace
    lines = [line.strip() for line in text.splitlines()]
    cleaned_text = "\n".join(line for line in lines if line)

    return cleaned_text
