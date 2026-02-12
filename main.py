import os
import shutil
from fastapi import FastAPI, Request, Form, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from db import get_user_by_username, verify_password, list_users, set_active_status, get_db_connection
from auth import make_session, read_session
from pdf_engine import build_pdf

app = FastAPI(title="نظام التقارير الطبية المطور")
templates = Jinja2Templates(directory="templates")

# وظيفة للحصول على المستخدم الحالي من الكوكيز
async def get_current_user(request: Request):
    session_token = request.cookies.get("session")
    if not session_token:
        return None
    username = read_session(session_token)
    if not username:
        return None
    return get_user_by_username(username)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user['is_active'] == 0:
        return HTMLResponse("حسابك معطل. يرجى التواصل مع المسؤول.", status_code=403)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = get_user_by_username(username)
    if not user or not verify_password(password, user['password']):
        return templates.TemplateResponse("login.html", {"request": request, "error": "اسم المستخدم أو كلمة المرور غير صحيحة"})
    
    if user['is_active'] == 0:
        return templates.TemplateResponse("login.html", {"request": request, "error": "هذا الحساب معطل"})

    response = RedirectResponse(url="/", status_code=302)
    token = make_session(username)
    response.set_cookie(key="session", value=token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response

@app.post("/generate")
async def generate_report(
    request: Request,
    user=Depends(get_current_user),
    leave_id: str = Form(...),
    name: str = Form(...),
    national_id: str = Form(...),
    nationality: str = Form(None),
    employer: str = Form(None),
    practitioner: str = Form(None),
    position: str = Form(None),
    admission_date: str = Form(None),
    discharge_date: str = Form(None)
):
    if not user or user['is_active'] == 0:
        return RedirectResponse(url="/login", status_code=302)

    data = {
        "leave_id": leave_id,
        "name": name,
        "national_id": national_id,
        "nationality": nationality,
        "employer": employer,
        "practitioner": practitioner,
        "position": position,
        "admission_date": admission_date,
        "discharge_date": discharge_date
    }

    try:
        file_path = build_pdf(data)
        return FileResponse(
            path=file_path, 
            filename=f"report_{leave_id}.pdf",
            background=None # سيتم حذف الملف يدوياً أو عبر مهمة خلفية في الإنتاج
        )
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return HTMLResponse("حدث خطأ أثناء توليد التقرير. يرجى المحاولة لاحقاً.", status_code=500)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, user=Depends(get_current_user)):
    if not user or user['is_admin'] == 0:
        return RedirectResponse(url="/", status_code=302)
    
    users = list_users()
    return templates.TemplateResponse("admin.html", {"request": request, "user": user, "users": users})

@app.post("/upload-template")
async def upload_template(request: Request, file: UploadFile, user=Depends(get_current_user)):
    if not user or user['is_admin'] == 0:
        raise HTTPException(status_code=403, detail="غير مسموح")

    os.makedirs("storage", exist_ok=True)
    with open("storage/template.pdf", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/user/toggle/{uid}")
async def toggle_user_status(uid: int, user=Depends(get_current_user)):
    if not user or user['is_admin'] == 0:
        raise HTTPException(status_code=403, detail="غير مسموح")
    
    # الحصول على الحالة الحالية (تبسيطاً سنقوم بتبديلها)
    conn = get_db_connection()
    current = conn.execute("SELECT is_active FROM users WHERE id=?", (uid,)).fetchone()
    if current:
        new_status = 1 if current['is_active'] == 0 else 0
        set_active_status(uid, new_status)
    conn.close()
    
    return RedirectResponse(url="/admin", status_code=302)
