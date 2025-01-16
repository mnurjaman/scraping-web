from flask import Flask, render_template, request, send_file, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import pandas as pd
import os
import certifi
from datetime import datetime

app = Flask(__name__)


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_domain(url):
    parsed_uri = urlparse(url)
    return "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)


def get_all_links(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(
            url, headers=headers, verify=certifi.where(), timeout=30
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links_data = []

        # Mengambil semua elemen <a>
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(url, href)

            if is_valid_url(full_url):
                link_data = {
                    "url": full_url,
                    "text": link.get_text(strip=True) or "[No Text]",
                    "title": link.get("title", ""),
                    "type": "Internal" if get_domain(url) in full_url else "External",
                }
                links_data.append(link_data)

        # Mengambil semua elemen yang memiliki atribut src
        for element in soup.find_all(src=True):
            src = element["src"]
            full_url = urljoin(url, src)

            if is_valid_url(full_url):
                link_data = {
                    "url": full_url,
                    "text": element.get("alt", "[No Text]"),
                    "title": element.get("title", ""),
                    "type": f"{element.name.upper()} Source",
                }
                links_data.append(link_data)

        return links_data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def crawl_website(start_url, max_pages=100, max_time=600):  # 10 menit maksimum
    if not is_valid_url(start_url):
        return {"status": "error", "message": "URL tidak valid"}

    start_time = time.time()
    base_domain = get_domain(start_url)
    visited = set()
    to_visit = {start_url}
    all_links = []
    internal_count = 0
    external_count = 0
    media_count = 0

    try:
        while (
            to_visit
            and len(visited) < max_pages
            and (time.time() - start_time) < max_time
        ):
            current_url = to_visit.pop()

            if current_url not in visited and base_domain in current_url:
                print(f"Mengunjungi: {current_url}")
                visited.add(current_url)

                links_data = get_all_links(current_url)

                for link_data in links_data:
                    if link_data["url"] not in [l["url"] for l in all_links]:
                        all_links.append(link_data)

                        if link_data["type"] == "Internal":
                            internal_count += 1
                            if link_data["url"] not in visited:
                                to_visit.add(link_data["url"])
                        elif link_data["type"] == "External":
                            external_count += 1
                        else:
                            media_count += 1

                time.sleep(1)

        summary = {
            "total_links": len(all_links),
            "internal_links": internal_count,
            "external_links": external_count,
            "media_links": media_count,
            "pages_crawled": len(visited),
            "time_taken": f"{time.time() - start_time:.2f} seconds",
        }

        return {"status": "success", "links": all_links, "summary": summary}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            return jsonify({"status": "error", "message": "URL tidak boleh kosong"})

        result = crawl_website(url)

        if result["status"] == "success":
            try:
                # Buat direktori static jika belum ada
                os.makedirs("static", exist_ok=True)

                # Generate nama file dengan timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                excel_filename = f"static/crawled_links_{timestamp}.xlsx"

                # Konversi data ke DataFrame
                df = pd.DataFrame(result["links"])

                # Buat worksheet untuk links dan summary
                with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="Links", index=False)

                    # Tambahkan summary ke sheet terpisah
                    summary_df = pd.DataFrame([result["summary"]])
                    summary_df.to_excel(writer, sheet_name="Summary", index=False)

                return jsonify(
                    {
                        "status": "success",
                        "message": "Crawling berhasil",
                        "links": result["links"],
                        "summary": result["summary"],
                        "excel_file": excel_filename,
                    }
                )
            except Exception as e:
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Error saat menyimpan file: {str(e)}",
                    }
                )
        else:
            return jsonify(result)

    return render_template("index.html")
