import os
import sys
import io
import zipfile
import threading
import webbrowser
from flask import Flask, request, send_file, render_template, jsonify
from PIL import Image

def resource_path(relative_path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

app = Flask(__name__, template_folder=resource_path('templates'))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    files = request.files.getlist('images')

    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Tidak ada file yang diupload'}), 400

    images = []
    for f in files:
        if f and allowed_file(f.filename):
            img = Image.open(f.stream).convert('RGB')
            images.append(img)

    if not images:
        return jsonify({'error': 'Format file tidak didukung. Gunakan PNG atau JPG.'}), 400

    pdf_buffer = io.BytesIO()
    if len(images) == 1:
        images[0].save(pdf_buffer, format='PDF', resolution=150)
    else:
        images[0].save(
            pdf_buffer,
            format='PDF',
            resolution=150,
            save_all=True,
            append_images=images[1:]
        )
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='hasil.pdf'
    )

@app.route('/convert_split', methods=['POST'])
def convert_split():
    files = request.files.getlist('images')

    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Tidak ada file yang diupload'}), 400

    zip_buffer = io.BytesIO()
    count = 0

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f and allowed_file(f.filename):
                img = Image.open(f.stream).convert('RGB')
                pdf_buf = io.BytesIO()
                img.save(pdf_buf, format='PDF', resolution=150)
                pdf_buf.seek(0)
                base_name = f.filename.rsplit('.', 1)[0]
                zf.writestr(f"{base_name}.pdf", pdf_buf.read())
                count += 1

    if count == 0:
        return jsonify({'error': 'Format file tidak didukung. Gunakan PNG atau JPG.'}), 400

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='hasil_pdf.zip'
    )

def open_browser():
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    timer = threading.Timer(1.5, open_browser)
    timer.start()
    app.run(host='127.0.0.1', port=5000, debug=False)
