from flask import render_template, request, jsonify
from app import app
from app.services import crawl_website


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
