import cv2
import os
from flask import Flask, render_template, request, send_file

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper dictionaries for character encoding
d = {chr(i): i for i in range(255)}
c = {i: chr(i) for i in range(255)}

def encrypt_image(img, message, passcode):
    n, m, z = 0, 0, 0
    message = passcode + message  # Combine passcode with the message for extra security
    for char in message:
        img[n, m, z] = d[char]
        n += 1
        m += 1
        z = (z + 1) % 3
        if n >= img.shape[0]:
            n = 0
            m += 1
        if m >= img.shape[1]:
            m = 0
    return img

def decrypt_image(img, message_length, passcode):
    n, m, z = 0, 0, 0
    decrypted_message = ""
    for _ in range(message_length + len(passcode)):
        decrypted_message += c[img[n, m, z]]
        n += 1
        m += 1
        z = (z + 1) % 3
        if n >= img.shape[0]:
            n = 0
            m += 1
        if m >= img.shape[1]:
            m = 0
    
    # Verify passcode
    if decrypted_message.startswith(passcode):
        return decrypted_message[len(passcode):]  # Return message without passcode
    else:
        return "Invalid passcode!"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get("action")
        passcode = request.form.get("passcode")
        
        if 'image' in request.files and passcode:
            image = request.files['image']
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)
            
            if action == "Encrypt":
                message = request.form.get('message')
                img = cv2.imread(image_path)
                if img is None:
                    return render_template('index.html', error="Invalid image file.")
                encrypted_img = encrypt_image(img, message, passcode)
                encrypted_path = os.path.join(app.config['UPLOAD_FOLDER'], "encrypted_" + image.filename)
                cv2.imwrite(encrypted_path, encrypted_img)
                return render_template('index.html', encrypted_image=encrypted_path, download_link=encrypted_path)
            
            elif action == "Decrypt":
                message_length = int(request.form.get('message_length', 100))  # Default length to 100
                img = cv2.imread(image_path)
                if img is None:
                    return render_template('index.html', error="Invalid image file.")
                decrypted_message = decrypt_image(img, message_length, passcode)
                return render_template('index.html', decrypted_message=decrypted_message)
    return render_template('index.html')

@app.route('/download/<filename>')
def download_image(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)