from flask import Flask, render_template, request, send_file
from PIL import Image
import io
import os
import shutil
import uuid

app = Flask(__name__)

# Ensure upload folder exists
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def cleanup_uploads():
    # Clean up all files in the uploads directory
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

@app.route('/', methods=['GET', 'POST'])
def image_processor():
    # Cleanup previous upload
    cleanup_uploads()
    
    if request.method == 'POST':
        # Check if file was uploaded
        if 'image' not in request.files:
            return render_template('index.html', error='No file uploaded')
        
        file = request.files['image']
        
        # Ensure filename is not empty
        if file.filename == '':
            return render_template('index.html', error='No selected file')

        try:
            # Get form parameters
            compression_quality = int(request.form.get('compression', 85))
            width = int(request.form.get('width') or 0)
            height = int(request.form.get('height') or 0)
            maintain_aspect = 'aspect_ratio' in request.form

            # Save original file temporarily
            original_path = os.path.join(UPLOAD_FOLDER, 'original_image.jpg')
            file.save(original_path)

            # Open the image
            original_image = Image.open(original_path)
            original_size = os.path.getsize(original_path)

            # Calculate new dimensions
            if maintain_aspect:
                # Maintain aspect ratio
                if width and height:
                    # If both are specified, use the more constraining dimension
                    original_ratio = original_image.width / original_image.height
                    new_ratio = width / height
                    
                    if new_ratio > original_ratio:
                        # Width is more constraining
                        width = int(height * original_ratio)
                    else:
                        # Height is more constraining
                        height = int(width / original_ratio)
                elif width:
                    # Scale based on width
                    height = int(width * (original_image.height / original_image.width))
                elif height:
                    # Scale based on height
                    width = int(height * (original_image.width / original_image.height))
            
            # Resize image
            if width and height:
                resized_image = original_image.resize((width, height), Image.LANCZOS)
            else:
                resized_image = original_image

            # Save processed image
            processed_path = os.path.join(UPLOAD_FOLDER, 'processed_image.jpg')
            resized_image.save(processed_path, optimize=True, quality=compression_quality)

            # Calculate new file size
            new_size = os.path.getsize(processed_path)
            size_reduction = (1 - (new_size / original_size)) * 100

            return render_template('index.html', 
                                   original_image='uploads/original_image.jpg', 
                                   processed_image='uploads/processed_image.jpg',
                                   original_size=f"{original_size/1024:.2f} KB",
                                   new_size=f"{new_size/1024:.2f} KB",
                                   size_reduction=f"{size_reduction:.2f}%",
                                   old_dimension=original_image.size,
                                   new_dimension=resized_image.size)

        except Exception as e:
            # Cleanup when error
            cleanup_uploads()
            return render_template('index.html', error=str(e))

    return render_template('index.html')

@app.before_request
def before_request():
    # Cleanup uploads before each request if it's a GET request to the root
    if request.method == 'GET' and request.path == '/':
        cleanup_uploads()
        
if __name__ == '__main__':
    app.run(debug=True)