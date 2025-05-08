# PDF to Enhanced Images Converter
# This notebook converts PDF pages to individual images with clarity enhancements

# Install required packages
!pip install pdf2image Pillow numpy matplotlib

# Import necessary libraries
import os
import numpy as np
import matplotlib.pyplot as plt
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
from google.colab import files
import io
import zipfile
from IPython.display import display, HTML

# Function to upload PDF file
def upload_pdf():
    """Upload a PDF file from local computer"""
    print("Please upload your PDF file...")
    uploaded = files.upload()
    
    if not uploaded:
        print("No file was uploaded.")
        return None
    
    pdf_path = list(uploaded.keys())[0]
    print(f"Successfully uploaded: {pdf_path}")
    return pdf_path

# Function to preprocess an image
def enhance_image(image, contrast_factor=1.5, sharpness_factor=1.5, brightness_factor=1.2):
    """
    Enhance image clarity by adjusting contrast, sharpness, and brightness
    
    Parameters:
    - image: PIL Image object
    - contrast_factor: float, contrast enhancement factor
    - sharpness_factor: float, sharpness enhancement factor
    - brightness_factor: float, brightness enhancement factor
    
    Returns:
    - Enhanced PIL Image object
    """
    # Convert to grayscale if needed (optional)
    # image = image.convert('L')
    
    # Apply a slight Gaussian blur to reduce noise (optional)
    image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Increase brightness
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness_factor)
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast_factor)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(sharpness_factor)
    
    return image

# Function to convert PDF to images with enhancements
def convert_pdf_to_enhanced_images(pdf_path, dpi=300, 
                                 contrast=1.5, sharpness=1.5, brightness=1.2,
                                 output_format='PNG'):
    """
    Convert PDF pages to enhanced images
    
    Parameters:
    - pdf_path: string, path to the PDF file
    - dpi: int, DPI for rendering PDF pages
    - contrast: float, contrast enhancement factor
    - sharpness: float, sharpness enhancement factor  
    - brightness: float, brightness enhancement factor
    - output_format: string, format for output images (PNG, JPEG, etc.)
    
    Returns:
    - List of paths to the generated image files
    """
    # Create output directory
    output_dir = 'enhanced_images'
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert PDF to images
    print(f"Converting PDF to images with DPI={dpi}...")
    images = convert_from_path(pdf_path, dpi=dpi)
    
    # Process each page
    image_paths = []
    for i, image in enumerate(images):
        # Enhance image clarity
        enhanced_image = enhance_image(
            image, 
            contrast_factor=contrast,
            sharpness_factor=sharpness,
            brightness_factor=brightness
        )
        
        # Save the enhanced image
        output_path = os.path.join(output_dir, f'page_{i+1}.{output_format.lower()}')
        enhanced_image.save(output_path, format=output_format)
        image_paths.append(output_path)
        
        print(f"Processed page {i+1}/{len(images)}")
    
    return image_paths

# Function to display sample images
def display_sample_images(image_paths, num_samples=3):
    """Display sample of the processed images for preview"""
    num_samples = min(num_samples, len(image_paths))
    samples = image_paths[:num_samples]
    
    # Create subplot grid
    fig, axes = plt.subplots(1, num_samples, figsize=(15, 5))
    if num_samples == 1:
        axes = [axes]
    
    # Display each sample image
    for i, path in enumerate(samples):
        img = Image.open(path)
        axes[i].imshow(np.array(img))
        axes[i].set_title(f"Page {i+1}")
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.show()

# Function to zip and download the enhanced images
def download_enhanced_images(image_paths):
    """Compress all enhanced images into a ZIP file and download it"""
    if not image_paths:
        print("No images to download.")
        return
    
    # Create a ZIP file in memory
    zip_filename = 'enhanced_images.zip'
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for path in image_paths:
            zip_file.write(path, os.path.basename(path))  # Ensure correct path in ZIP file
    
    # Save the ZIP file to disk
    with open(zip_filename, 'wb') as f:
        f.write(zip_buffer.getvalue())

    # Download the ZIP file
    files.download(zip_filename)
    print("Download started for enhanced_images.zip")


# Interactive control panel with sliders
def create_control_panel(pdf_path):
    """Create an interactive control panel for image enhancement parameters"""
    from ipywidgets import interact, interactive, fixed, widgets
    
    # Define the process function that will be called by the interactive widgets
    def process_with_params(dpi, contrast, sharpness, brightness, format_choice):
        # Map format choice to actual format
        format_map = {
            'PNG - Best Quality': 'PNG',
            'JPEG - Smaller Size': 'JPEG',
            'TIFF - High Quality': 'TIFF'
        }
        output_format = format_map[format_choice]
        
        # Process the PDF with the selected parameters
        image_paths = convert_pdf_to_enhanced_images(
            pdf_path, 
            dpi=dpi, 
            contrast=contrast, 
            sharpness=sharpness, 
            brightness=brightness,
            output_format=output_format
        )
        
        # Display samples
        display_sample_images(image_paths)
        
        # Provide download button
        download_button = widgets.Button(
            description='Download All Images',
            button_style='success'
        )
        
        def on_download_button_clicked(b):
            download_enhanced_images(image_paths)
        
        download_button.on_click(on_download_button_clicked)
        display(download_button)
    
    # Create the interactive widget
    interact(
        process_with_params,
        dpi=widgets.IntSlider(min=100, max=600, step=50, value=300, description='DPI:'),
        contrast=widgets.FloatSlider(min=0.5, max=2.5, step=0.1, value=1.5, description='Contrast:'),
        sharpness=widgets.FloatSlider(min=0.5, max=2.5, step=0.1, value=1.5, description='Sharpness:'),
        brightness=widgets.FloatSlider(min=0.5, max=2.0, step=0.1, value=1.2, description='Brightness:'),
        format_choice=widgets.Dropdown(
            options=['PNG - Best Quality', 'JPEG - Smaller Size', 'TIFF - High Quality'],
            value='PNG - Best Quality',
            description='Format:'
        )
    )

# Main execution
def main():
    print("PDF to Enhanced Images Converter")
    print("================================")
    print("This tool will convert each page of a PDF to separate images")
    print("with enhanced clarity and allow you to download them.")
    print("")
    
    # Step 1: Upload PDF
    pdf_path = upload_pdf()
    if pdf_path is None:
        return
    
    # Step 2: Show control panel for processing options
    print("\nUse the controls below to adjust enhancement settings:")
    create_control_panel(pdf_path)

# Run the main function
main()