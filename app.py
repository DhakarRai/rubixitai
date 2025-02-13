from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# Add cache control headers
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.expires = 0
    response.cache_control.public = False
    return response

@app.route('/')
def home():
    return render_template('webpagerubix1.html')

# Add new route for parent page
@app.route('/parent')
def parent():
    return render_template('parent.html')

# Add route for chat page
@app.route('/chat')
def chat():
    return render_template('main1.1.html')

# Add route for subjects page
@app.route('/subjects')
def subjects():
    return render_template('index.html')

# Add a specific route for the logo
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)

if __name__ == '__main__':
    app.run(debug=True)