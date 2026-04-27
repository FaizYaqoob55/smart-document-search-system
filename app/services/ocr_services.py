import pytesseract
from PIL import Image, ImageFilter
from pdf2image import convert_from_path
import PyPDF2
import os


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def correct_rotataion(image):
    try :
        osd = pytesseract.image_to_osd(image)
        rotation = int(osd.split("Rotate: ")[1].split("\n")[0])
        if rotation != 0:
            image = image.rotate(-rotation, expand=True)
    except :
        pass
    return image


   



# def preprocess_image(image):
#     image = correct_rotataion(image)
#     image = image.convert('L')
# # contrast improve
#     image=image.point(lambda x: 0 if x < 140 else 255)
#     #denoise
#     image=image.filter(ImageFilter.MedianFilter())
#     return image 


# img=Image.open(r"F:\smart-document-search-system\test.png")
# text=pytesseract.image_to_string((img))
# print(text)

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    image = preprocess_image(image)
    text = pytesseract.image_to_string(image)

    # confidence score nikalne ke liye
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    conf_score = [int(conf) for conf in data['conf'] if conf != '-1']
    avg_conf= sum(conf_score) / len(conf_score) if conf_score else 0
    print("Average OCR Confidence:", avg_conf)

    return text, avg_conf





def extract_text_from_scanned_pdf(pdf_path):
    # Use relative path to poppler folder in current project
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    poppler_path = os.path.join(project_root, "poppler", "poppler-23.08.0", "Library", "bin")
    print(f'DEBUG: Poppler path: {poppler_path}')
    print(f'DEBUG: Path exists: {os.path.exists(poppler_path)}')
    pages=convert_from_path(pdf_path, poppler_path=poppler_path)
    full_text=""
    for i,page in enumerate(pages):
        page=preprocess_image(page)
        text=pytesseract.image_to_string(page)


        data=pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT)
        conf_score=[int(conf) for conf in data['conf'] if conf != '-1']
        avg_conf=sum(conf_score)/len(conf_score) if conf_score else 0

        print(f"Page {i+1} ORC done with confidence {avg_conf}") 
        full_text+=text+"\n"
    return full_text

def is_scanned_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
        for page in reader.pages:
            text += page.extract_text()or ""
        return len(text.strip()) < 50
    except:
        return True











from PIL import Image, ImageEnhance, ImageFilter
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract


def preprocess_image(image):

    image = image.convert("RGB")

    image = image.convert("L")

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(3)

    image = image.filter(ImageFilter.SHARPEN)

    return image


def extract_text_from_tiff(image_path):
    image = Image.open(image_path)

    full_text = ""
    all_conf = []

    total_pages = getattr(image, "n_frames", 1)

    print("Total pages:", total_pages)

    for page in range(total_pages):
        image.seek(page)
        current_page = image.copy()
        current_page = preprocess_image(current_page)

        text = pytesseract.image_to_string(
            current_page,
            config="--psm 6"
        )

        data = pytesseract.image_to_data(current_page, output_type=pytesseract.Output.DICT)
        conf_scores = [int(c) for c in data["conf"] if c != "-1"]

        if conf_scores:
            all_conf.append(sum(conf_scores) / len(conf_scores))

        print(f"PAGE {page+1} TEXT:", text)
        full_text += f"\n--- PAGE {page+1} ---\n{text}"

    avg_conf = sum(all_conf) / len(all_conf) if all_conf else 0

    return full_text, avg_conf