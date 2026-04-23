import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageStat
import numpy as np
import os
from datetime import datetime
import json

class ImageAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Statistics Analyzer")
        self.root.geometry("1000x700")
        self.image_path = None
        self.image = None
        self.img_array = None
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Top frame for file selection
        top_frame = ttk.Frame(root, padding="10")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        ttk.Button(top_frame, text="Select Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(top_frame, text="No image selected", foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(top_frame, text="Export Stats", command=self.export_stats).pack(side=tk.RIGHT, padx=5)
        
        # Left frame for image preview
        left_frame = ttk.LabelFrame(root, text="Image Preview", padding="10")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.image_label = tk.Label(left_frame, bg="gray", width=30, height=20)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Right frame for statistics
        right_frame = ttk.LabelFrame(root, text="Image Statistics", padding="10")
        right_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        
        # Scrollable frame for stats
        self.canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif *.webp"), 
                      ("All files", "*.*")]
        )
        
        if file_path:
            self.image_path = file_path
            self.file_label.config(text=os.path.basename(file_path), foreground="black")
            self.analyze_image()
    
    def analyze_image(self):
        try:
            self.image = Image.open(self.image_path)
            self.img_array = np.array(self.image)
            
            # Display thumbnail
            self.display_thumbnail()
            
            # Calculate and display statistics
            self.display_statistics()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def display_thumbnail(self):
        # Create thumbnail
        thumb = self.image.copy()
        thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
        
        from PIL import ImageTk
        self.photo_image = ImageTk.PhotoImage(thumb)
        self.image_label.config(image=self.photo_image)
    
    def display_statistics(self):
        # Clear previous stats
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        stats = self.calculate_statistics()
        
        # Display each category
        for category, values in stats.items():
            self.add_category_frame(category, values)
    
    def calculate_statistics(self):
        stats = {}
        
        # File Information
        file_stats = {}
        file_size = os.path.getsize(self.image_path)
        file_stats["File Name"] = os.path.basename(self.image_path)
        file_stats["File Path"] = self.image_path
        file_stats["File Size"] = self.format_size(file_size)
        file_stats["Last Modified"] = datetime.fromtimestamp(os.path.getmtime(self.image_path)).strftime("%Y-%m-%d %H:%M:%S")
        stats["📁 File Information"] = file_stats
        
        # Image Properties
        img_props = {}
        img_props["Width"] = f"{self.image.width} px"
        img_props["Height"] = f"{self.image.height} px"
        img_props["Total Pixels"] = f"{self.image.width * self.image.height:,}"
        img_props["Aspect Ratio"] = f"{self.image.width / self.image.height:.2f}"
        img_props["Format"] = self.image.format or "Unknown"
        img_props["Mode"] = self.image.mode
        
        # Bit depth
        if self.image.mode == "RGB":
            img_props["Bit Depth"] = "24-bit (8 bits per channel)"
            img_props["Color Channels"] = "3 (RGB)"
        elif self.image.mode == "RGBA":
            img_props["Bit Depth"] = "32-bit (8 bits per channel + alpha)"
            img_props["Color Channels"] = "4 (RGBA)"
        elif self.image.mode == "L":
            img_props["Bit Depth"] = "8-bit (Grayscale)"
            img_props["Color Channels"] = "1"
        else:
            img_props["Bit Depth"] = f"Unknown ({self.image.mode})"
        
        stats["🖼️ Image Properties"] = img_props
        
        # Pixel Statistics
        pixel_stats = self.calculate_pixel_statistics()
        stats["📊 Pixel Statistics"] = pixel_stats
        
        # Color Statistics
        if self.image.mode in ["RGB", "RGBA"]:
            color_stats = self.calculate_color_statistics()
            stats["🎨 Color Statistics"] = color_stats
        
        # Noise Estimation (for JPG)
        noise_stats = self.estimate_noise()
        stats["🔊 Noise Analysis"] = noise_stats
        
        # Quality Metrics
        quality_stats = self.calculate_quality_metrics()
        stats["⚙️ Quality Metrics"] = quality_stats
        
        return stats
    
    def calculate_pixel_statistics(self):
        stats = {}
        
        # Flatten array
        flat_array = self.img_array.flatten().astype(float)
        
        stats["Min Pixel Value"] = f"{int(np.min(self.img_array))}"
        stats["Max Pixel Value"] = f"{int(np.max(self.img_array))}"
        stats["Mean Pixel Value"] = f"{np.mean(flat_array):.2f}"
        stats["Median Pixel Value"] = f"{int(np.median(flat_array))}"
        stats["Std Deviation"] = f"{np.std(flat_array):.2f}"
        stats["Variance"] = f"{np.var(flat_array):.2f}"
        
        # Dynamic range
        dynamic_range = np.max(self.img_array) - np.min(self.img_array)
        stats["Dynamic Range"] = f"{dynamic_range} levels"
        
        return stats
    
    def calculate_color_statistics(self):
        stats = {}
        
        if self.image.mode == "RGBA":
            channels = ["Red", "Green", "Blue", "Alpha"]
        else:
            channels = ["Red", "Green", "Blue"]
        
        for i, channel_name in enumerate(channels[:len(self.img_array.shape)]):
            if len(self.img_array.shape) == 3 and i < self.img_array.shape[2]:
                channel_data = self.img_array[:, :, i].flatten().astype(float)
                stats[f"{channel_name} Mean"] = f"{np.mean(channel_data):.2f}"
                stats[f"{channel_name} Std Dev"] = f"{np.std(channel_data):.2f}"
        
        return stats
    
    def estimate_noise(self):
        stats = {}
        
        if len(self.img_array.shape) == 3:
            # Convert to grayscale for noise estimation
            gray = np.dot(self.img_array[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = self.img_array.astype(float)
        
        # Estimate noise using Laplacian filter (high-freq content)
        laplacian = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])
        edges = np.sqrt(np.mean(np.abs(gray) ** 2))
        
        # Local contrast (noise proxy)
        local_std = np.std(gray)
        stats["Estimated Noise Level (Std)"] = f"{local_std:.2f}"
        
        # Estimate SNR (simplified)
        mean_val = np.mean(gray)
        if mean_val > 0:
            snr_db = 20 * np.log10(mean_val / (local_std + 1e-6))
            stats["Estimated SNR (dB)"] = f"{snr_db:.2f} dB*"
        
        stats["⚠️ Note"] = "* JPG SNR is not accurate due to compression"
        
        return stats
    
    def calculate_quality_metrics(self):
        stats = {}
        
        # Convert to grayscale
        if len(self.img_array.shape) == 3:
            gray = np.dot(self.img_array[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = self.img_array.astype(float)
        
        # Sharpness (Laplacian variance)
        laplacian = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])
        edges = np.abs(gray).std()
        stats["Sharpness Estimate"] = f"{edges:.2f} (higher = sharper)"
        
        # Contrast
        contrast = np.max(gray) - np.min(gray)
        stats["Contrast"] = f"{contrast:.0f} levels"
        
        # Brightness
        brightness = np.mean(gray)
        stats["Brightness"] = f"{brightness:.0f} (0-255 scale)"
        
        # Saturation (if RGB)
        if len(self.img_array.shape) == 3:
            r = self.img_array[:, :, 0].astype(float)
            g = self.img_array[:, :, 1].astype(float)
            b = self.img_array[:, :, 2].astype(float)
            
            max_rgb = np.maximum(np.maximum(r, g), b)
            min_rgb = np.minimum(np.minimum(r, g), b)
            
            delta = max_rgb - min_rgb
            saturation = np.mean(delta)
            stats["Saturation Estimate"] = f"{saturation:.2f}"
        
        # Compression artifacts (JPG specific)
        if self.image.format == "JPEG":
            # Detect blocking artifacts (common in JPG)
            blocking_score = self.detect_blocking_artifacts()
            stats["JPG Blocking Artifacts"] = f"{blocking_score:.2f} (higher = more artifacts)"
        
        return stats
    
    def detect_blocking_artifacts(self):
        """Detect 8x8 blocking artifacts typical of JPEG compression"""
        if len(self.img_array.shape) == 3:
            gray = np.dot(self.img_array[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = self.img_array.astype(float)
        
        # Check for discontinuities at 8x8 block boundaries
        score = 0
        for y in range(8, gray.shape[0], 8):
            score += np.mean(np.abs(np.diff(gray[y-1:y+1, :], axis=0)))
        for x in range(8, gray.shape[1], 8):
            score += np.mean(np.abs(np.diff(gray[:, x-1:x+1], axis=1)))
        
        return score / 10  # Normalize
    
    def add_category_frame(self, category_name, values_dict):
        """Add a category frame with stat items"""
        cat_frame = ttk.LabelFrame(self.scrollable_frame, text=category_name, padding="8")
        cat_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for key, value in values_dict.items():
            row_frame = ttk.Frame(cat_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)
            
            label = ttk.Label(row_frame, text=f"{key}:", font=("", 10, "bold"), width=25, anchor="w")
            label.pack(side=tk.LEFT, fill=tk.X)
            
            value_label = ttk.Label(row_frame, text=str(value), foreground="darkblue")
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def format_size(self, size_bytes):
        """Convert bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def export_stats(self):
        if self.image_path is None:
            messagebox.showwarning("Warning", "Please select an image first")
            return
        
        stats = self.calculate_statistics()
        
        # Flatten stats for export
        flat_stats = {}
        for category, values in stats.items():
            flat_stats[category] = values
        
        # Save as JSON
        export_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{os.path.splitext(os.path.basename(self.image_path))[0]}_stats.json"
        )
        
        if export_path:
            with open(export_path, 'w') as f:
                json.dump(flat_stats, f, indent=2)
            messagebox.showinfo("Success", f"Statistics exported to:\n{export_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnalyzerGUI(root)
    root.mainloop()
