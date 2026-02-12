import os
import uuid
import qrcode
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader, PdfWriter

from utils_ar import ar
from config import settings

# تسجيل الخط العربي
pdfmetrics.registerFont(TTFont("arabic", settings.FONT_PATH))

# مواقع الحقول على قالب الـ PDF (يمكن تعديلها حسب القالب)
POSITIONS = {
    "leave_id": (260, 640),
    "name": (260, 490),
    "national_id": (260, 460),
    "nationality": (260, 430),
    "employer": (260, 400),
    "practitioner": (260, 370),
    "position": (260, 340),
    "admission_date": (260, 310),
    "discharge_date": (260, 280),
}

def build_pdf(data):
    # إنشاء معرف فريد للعملية
    job_id = str(uuid.uuid4())[:8]
    overlay_path = f"overlay_{job_id}.pdf"
    output_path = f"report_{job_id}.pdf"
    qr_path = f"qr_{job_id}.png"

    try:
        # 1. إنشاء طبقة النصوص (Overlay)
        c = canvas.Canvas(overlay_path)
        c.setFont("arabic", 12)
        c.setFillColor(HexColor(settings.TEXT_COLOR))

        for key, value in data.items():
            if key in POSITIONS and value:
                x, y = POSITIONS[key]
                text = ar(str(value))
                # محاكاة الخط العريض (Bold)
                for i in range(settings.BOLD_STEPS):
                    c.drawString(x + i * settings.BOLD_OFFSET, y, text)

        # 2. إضافة رمز QR إذا وجد معرف الإجازة
        if data.get("leave_id"):
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(data["leave_id"])
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_path)
            c.drawImage(qr_path, 70, 120, 90, 90)

        c.save()

        # 3. دمج الطبقة مع القالب الأساسي
        template_path = "storage/template.pdf"
        if not os.path.exists(template_path):
            # إذا لم يوجد قالب، نكتفي بطبقة النصوص كملف ناتج
            os.rename(overlay_path, output_path)
        else:
            base_pdf = PdfReader(template_path)
            overlay_pdf = PdfReader(overlay_path)
            
            output_writer = PdfWriter()
            page = base_pdf.pages[0]
            page.merge_page(overlay_pdf.pages[0])
            output_writer.add_page(page)

            with open(output_path, "wb") as f:
                output_writer.write(f)

        return output_path

    finally:
        # تنظيف الملفات المؤقتة
        for path in [overlay_path, qr_path]:
            if os.path.exists(path):
                os.remove(path)
