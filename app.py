from flask import Flask, render_template, request, jsonify
from PIL import Image
from PIL.ExifTags import TAGS
import numpy as np
import os
from datetime import datetime
import io
import base64
import json
from scipy import stats as scipy_stats

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp'

def detect_camera_type(image_path, image, img_array):
    """Detect camera type: RGB, Thermal, IR, TOF, etc."""
    detection = {
        'likely_type': 'Unknown',
        'confidence': 0,
        'analysis': {}
    }
    
    # Get EXIF metadata
    exif_data = {}
    try:
        exif_dict = image._getexif()
        if exif_dict:
            for tag_id, value in exif_dict.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
    except:
        pass
    
    # Analyze metadata
    if exif_data:
        model = exif_data.get('Model', '').lower()
        detection['analysis']['camera_model'] = model
        
        if 'thermal' in model or 'flir' in model or 'boson' in model:
            detection['likely_type'] = 'Thermal Camera'
            detection['confidence'] = 95
            return detection
        elif 'ir' in model or 'infrared' in model:
            detection['likely_type'] = 'IR Camera'
            detection['confidence'] = 90
            return detection
    
    # Analyze image properties
    if len(img_array.shape) == 3:
        channels = img_array.shape[2]
    else:
        channels = 1
    
    detection['analysis']['channels'] = channels
    detection['analysis']['shape'] = f"{img_array.shape}"
    
    # Bit depth analysis
    bit_depth = img_array.dtype
    detection['analysis']['dtype'] = str(bit_depth)
    
    # Convert to grayscale for analysis
    if len(img_array.shape) == 3:
        gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
    else:
        gray = img_array.astype(np.float32)
    
    # Statistical analysis
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    skewness = scipy_stats.skew(gray.flatten())
    kurtosis = scipy_stats.kurtosis(gray.flatten())
    
    detection['analysis']['skewness'] = f"{skewness:.3f}"
    detection['analysis']['kurtosis'] = f"{kurtosis:.3f}"
    
    # Histogram analysis
    hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
    entropy = -np.sum((hist / hist.sum()) * np.log2(hist / hist.sum() + 1e-7))
    detection['analysis']['entropy'] = f"{entropy:.2f}"
    
    # Color distribution analysis
    if channels == 3:
        r = img_array[..., 0].astype(np.float32)
        g = img_array[..., 1].astype(np.float32)
        b = img_array[..., 2].astype(np.float32)
        
        r_mean, g_mean, b_mean = np.mean(r), np.mean(g), np.mean(b)
        detection['analysis']['r_mean'] = f"{r_mean:.1f}"
        detection['analysis']['g_mean'] = f"{g_mean:.1f}"
        detection['analysis']['b_mean'] = f"{b_mean:.1f}"
        
        # Check for RGB balance
        color_ratio = max(r_mean, g_mean, b_mean) / (min(r_mean, g_mean, b_mean) + 1)
        detection['analysis']['color_balance_ratio'] = f"{color_ratio:.2f}"
        
        # Thermal images often have pseudo-coloring
        # Check if image is pseudo-colored thermal (strong color variation)
        if color_ratio > 2.5:
            detection['likely_type'] = 'Pseudo-Colored Thermal/IR'
            detection['confidence'] = 60
            return detection
        
        # Normal RGB camera
        if color_ratio < 1.5:
            detection['likely_type'] = 'RGB Camera'
            detection['confidence'] = 85
            return detection
    
    # 1 channel - grayscale analysis
    elif channels == 1:
        # Check for TOF characteristics
        # TOF images often have specific depth value ranges and patterns
        
        # TOF-specific detection
        tof_score = 0
        
        # Check bit depth (TOF typically 12-16 bit)
        if img_array.dtype in [np.uint16, np.int16]:
            tof_score += 20
            # Check for typical TOF value ranges (usually 0-4095 or 0-65535)
            max_val = np.max(img_array)
            if max_val < 4096:  # Typical 12-bit TOF
                tof_score += 30
                detection['analysis']['tof_bits'] = '12-bit'
            elif max_val < 16384:  # 14-bit TOF
                tof_score += 25
                detection['analysis']['tof_bits'] = '14-bit'
            
            # Check spatial coherence (TOF has strong spatial smoothness)
            if img_array.shape[0] > 10 and img_array.shape[1] > 10:
                # Calculate local variance
                diff_vertical = np.abs(np.diff(img_array, axis=0))
                diff_horizontal = np.abs(np.diff(img_array, axis=1))
                coherence = 1.0 / (np.mean(diff_vertical) + np.mean(diff_horizontal) + 1)
                
                if coherence > 0.95:  # High spatial coherence
                    tof_score += 25
                    detection['analysis']['spatial_coherence'] = f"{coherence:.3f}"
            
            # Left-skewed histogram (background/max distance at max value)
            if skewness < -0.5:
                tof_score += 15
                detection['analysis']['histogram_skewness'] = f"{skewness:.3f}"
            
            # Check for invalid pixel markers (often 0 or max value in TOF)
            zero_pixels = np.sum(img_array == 0) / img_array.size
            max_pixels = np.sum(img_array == max_val) / img_array.size
            
            if zero_pixels > 0.05 or max_pixels > 0.05:  # Invalid pixels
                tof_score += 10
                detection['analysis']['invalid_pixels'] = f"{(zero_pixels + max_pixels)*100:.1f}%"
        
        # Make decision based on TOF score
        if tof_score > 60:
            detection['likely_type'] = 'TOF (Time-of-Flight) Depth Camera'
            detection['confidence'] = min(95, tof_score)
            return detection
        elif img_array.dtype in [np.uint16, np.int16]:
            detection['likely_type'] = 'Thermal/IR Camera (16-bit)'
            detection['confidence'] = 75
            return detection
        
        # 8-bit grayscale
        if entropy < 4.0:  # Low entropy suggests structured data (thermal, depth)
            if std_val < 15:  # Low variation
                detection['likely_type'] = 'Thermal/IR Camera'
                detection['confidence'] = 65
            else:
                detection['likely_type'] = 'Grayscale/IR Camera'
                detection['confidence'] = 55
        else:
            detection['likely_type'] = 'Grayscale/IR Camera'
            detection['confidence'] = 50
        
        return detection
    
    detection['confidence'] = 40
    return detection

def analyze_image(image_path):
    """Comprehensive image analysis"""
    stats = {}
    
    # Load image
    image = Image.open(image_path)
    img_array = np.array(image)
    
    # Camera type detection
    camera_detection = detect_camera_type(image_path, image, img_array)
    stats['camera_type'] = camera_detection
    
    # File Information
    file_size = os.path.getsize(image_path)
    stats['file'] = {
        'name': os.path.basename(image_path),
        'path': image_path,
        'size': format_size(file_size),
        'modified': datetime.fromtimestamp(os.path.getmtime(image_path)).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Image Properties
    stats['properties'] = {
        'width': f"{image.width} px",
        'height': f"{image.height} px",
        'total_pixels': f"{image.width * image.height:,}",
        'aspect_ratio': f"{image.width / image.height:.2f}",
        'format': image.format or 'Unknown',
        'mode': image.mode
    }
    
    # Determine bit depth
    if image.mode == "RGB":
        stats['properties']['bit_depth'] = "24-bit (8 bits per channel)"
        stats['properties']['channels'] = "3 (RGB)"
    elif image.mode == "RGBA":
        stats['properties']['bit_depth'] = "32-bit (8 bits per channel + alpha)"
        stats['properties']['channels'] = "4 (RGBA)"
    elif image.mode == "L":
        stats['properties']['bit_depth'] = "8-bit (Grayscale)"
        stats['properties']['channels'] = "1"
    else:
        stats['properties']['bit_depth'] = f"Unknown ({image.mode})"
    
    # Pixel Statistics
    flat_array = img_array.flatten().astype(float)
    stats['pixels'] = {
        'min': f"{int(np.min(img_array))}",
        'max': f"{int(np.max(img_array))}",
        'mean': f"{np.mean(flat_array):.2f}",
        'median': f"{int(np.median(flat_array))}",
        'std_dev': f"{np.std(flat_array):.2f}",
        'variance': f"{np.var(flat_array):.2f}",
        'dynamic_range': f"{np.max(img_array) - np.min(img_array)} levels"
    }
    
    # Color Statistics
    if image.mode == "RGBA":
        channels = ["Red", "Green", "Blue", "Alpha"]
    else:
        channels = ["Red", "Green", "Blue"]
    
    stats['color'] = {}
    for i, channel_name in enumerate(channels):
        if len(img_array.shape) == 3 and i < img_array.shape[2]:
            channel_data = img_array[:, :, i].flatten().astype(float)
            stats['color'][f'{channel_name}_mean'] = f"{np.mean(channel_data):.2f}"
            stats['color'][f'{channel_name}_std'] = f"{np.std(channel_data):.2f}"
    
    # Convert to grayscale for noise/quality analysis
    if len(img_array.shape) == 3:
        gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114])
    else:
        gray = img_array.astype(float)
    
    # Noise Analysis
    local_std = np.std(gray)
    mean_val = np.mean(gray)
    stats['noise'] = {
        'estimated_noise_level': f"{local_std:.2f}",
        'estimated_snr_db': f"{20 * np.log10(mean_val / (local_std + 1e-6)):.2f} dB*",
        'note': '* JPG SNR is not accurate due to compression'
    }
    
    # Quality Metrics
    edges = np.abs(gray).std()
    contrast = np.max(gray) - np.min(gray)
    brightness = np.mean(gray)
    
    stats['quality'] = {
        'sharpness': f"{edges:.2f} (higher = sharper)",
        'contrast': f"{contrast:.0f} levels",
        'brightness': f"{brightness:.0f} (0-255 scale)"
    }
    
    if len(img_array.shape) == 3:
        r = img_array[:, :, 0].astype(float)
        g = img_array[:, :, 1].astype(float)
        b = img_array[:, :, 2].astype(float)
        
        max_rgb = np.maximum(np.maximum(r, g), b)
        min_rgb = np.minimum(np.minimum(r, g), b)
        delta = max_rgb - min_rgb
        saturation = np.mean(delta)
        stats['quality']['saturation'] = f"{saturation:.2f}"
    
    # JPG blocking artifacts
    if image.format == "JPEG":
        blocking_score = 0
        for y in range(8, gray.shape[0], 8):
            blocking_score += np.mean(np.abs(np.diff(gray[y-1:y+1, :], axis=0)))
        for x in range(8, gray.shape[1], 8):
            blocking_score += np.mean(np.abs(np.diff(gray[:, x-1:x+1], axis=1)))
        stats['quality']['jpg_artifacts'] = f"{blocking_score / 10:.2f} (higher = more artifacts)"
    
    return stats, image

def format_size(size_bytes):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def image_to_base64(image, max_size=300):
    """Convert PIL image to base64 for display"""
    img_copy = image.copy()
    img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    buffered = io.BytesIO()
    img_copy.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Save temporarily
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Analyze
        stats, image = analyze_image(file_path)
        
        # Convert image to base64
        image_b64 = image_to_base64(image)
        
        return jsonify({
            'success': True,
            'image': image_b64,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
