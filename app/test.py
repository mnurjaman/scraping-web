from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)


def scrape_website(url):
    try:
        # Kirim request ke website
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Ambil data yang dibutuhkan
        title = soup.title.string if soup.title else "No title found"

        # Cari gambar pertama atau thumbnail
        image = ""
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            image = img_tag["src"]
            if not image.startswith("http"):
                image = url + image if image.startswith("/") else url + "/" + image

        # Ambil konten text
        content = ""
        paragraphs = soup.find_all("p")
        content = " ".join([p.text.strip() for p in paragraphs])

        return {
            "link": url,
            "image": image,
            "title": title,
            "content": content[:500] + "..." if len(content) > 500 else content,
        }
    except Exception as e:
        return {"link": url, "image": "Error", "title": "Error", "content": str(e)}


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        url = request.form["url"]
        if url:
            result = scrape_website(url)
    return render_template("home.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
