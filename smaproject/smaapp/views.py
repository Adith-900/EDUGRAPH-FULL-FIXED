import os
import re
import pdfplumber
from collections import defaultdict
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.template.loader import get_template
from django.http import HttpResponse
from django.db import transaction
from datetime import datetime
from .models import Student, FailedSubject
from xhtml2pdf import pisa  # Using xhtml2pdf
from django.core.cache import cache  # Ensure this import is present


def check_pass_fail_and_sgpa(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    # Extract Examination Name
    exam_match = re.search(r'Examination[:\s]*(.+)', text)

    exam_name = exam_match.group(1).strip() if exam_match else "Unknown"

    # Extract Programme Name
    programme_match = re.search(r"Programme (.+)", text)
    programme_name = programme_match.group(1).strip() if programme_match else "Unknown"

    student_name = next((line.replace("Name ", "").strip() for line in text.split("\n") if line.startswith("Name ")), "Unknown")
    sgpa_match = re.search(r"SGPA\s*:\s*([\d.]+)", text)
    sgpa = float(sgpa_match.group(1)) if sgpa_match else 0.0

    failed_subjects = [" ".join(line.split()[1:-4]).rsplit(" ", 1)[0].strip() 
                        for line in text.split("\n") if line.endswith("Failed")]

    return ("fail" if failed_subjects else "pass"), student_name, failed_subjects, sgpa, exam_name, programme_name

def clear_results_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

def process_pdfs(request):
    if request.method == 'POST' and request.FILES.getlist('pdf_files'):
        Student.objects.all().delete()
        FailedSubject.objects.all().delete()

        exam_name = "Unknown"
        programme_name = "Unknown"

        for pdf_file in request.FILES.getlist('pdf_files'):
            file_path = default_storage.save(pdf_file.name, pdf_file)
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            result, student_name, failed_subjects, sgpa, exam_name, programme_name = check_pass_fail_and_sgpa(full_path)
            student = Student.objects.create(name=student_name, sgpa=sgpa, result=result)
            FailedSubject.objects.bulk_create([FailedSubject(student=student, subject_name=subj) for subj in failed_subjects])
            os.remove(full_path)

        # Store in session instead of cache
        request.session['exam_name'] = exam_name
        request.session['programme_name'] = programme_name

        return redirect('results')
    return render(request, 'upload.html')

def show_results(request):
    students = Student.objects.all()
    failed_students = Student.objects.filter(result='fail')

    subject_fail_count = defaultdict(int)
    for student in failed_students:
        for subject in student.failed_subjects.all():
            subject_fail_count[subject.subject_name] += 1

    sorted_students = sorted(students, key=lambda s: s.sgpa, reverse=True)
    
    top_ranks = []
    prev_sgpa = None
    rank = 0

    for student in sorted_students:
        if prev_sgpa is None or student.sgpa != prev_sgpa:
            rank += 1
            if rank > 3:
                break
            top_ranks.append((rank, [(student.name, student.sgpa)]))
        else:
            top_ranks[-1][1].append((student.name, student.sgpa))

        prev_sgpa = student.sgpa

    context = {
    'total_students': students.count(),
    'total_pass': students.filter(result='pass').count(),
    'total_fail': students.filter(result='fail').count(),
    'failed_students': failed_students,
    'subject_fail_count': list(subject_fail_count.items()),
    'top_students': top_ranks,
    'current_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'exam_name': request.session.get('exam_name', 'Unknown'),  # Using session
    'programme_name': request.session.get('programme_name', 'Unknown')  # Using session
}


    return render(request, 'results.html', context)

def generate_pdf(html_content):
    result = HttpResponse(content_type='application/pdf')
    result['Content-Disposition'] = 'attachment; filename="results.pdf"'
    pisa_status = pisa.CreatePDF(html_content, dest=result)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", content_type='text/plain')
    return result

def download_results_pdf(request):
    students = Student.objects.all()
    failed_students = Student.objects.filter(result='fail')
    
    subject_fail_count = defaultdict(int)
    for student in failed_students:
        for subject in student.failed_subjects.all():
            subject_fail_count[subject.subject_name] += 1

    sorted_students = sorted(students, key=lambda s: s.sgpa, reverse=True)
    
    top_ranks = []
    prev_sgpa = None
    rank = 0

    for student in sorted_students:
        if prev_sgpa is None or student.sgpa != prev_sgpa:
            rank += 1
            if rank > 3:
                break
            top_ranks.append((rank, [(student.name, student.sgpa)]))
        else:
            top_ranks[-1][1].append((student.name, student.sgpa))

        prev_sgpa = student.sgpa

    now = datetime.now()
    current_date = now.strftime('%d/%m/%y')  
    current_time = now.strftime('%I:%M %p')  
    
    context = {
        'total_students': students.count(),
        'total_pass': students.filter(result='pass').count(),
        'total_fail': students.filter(result='fail').count(),
        'failed_students': failed_students,
        'subject_fail_count': list(subject_fail_count.items()),
        'top_students': top_ranks,
        'current_date': current_date,
        'current_time': current_time,
        'exam_name': request.session.get('exam_name', 'Unknown'),  # Using session
        'programme_name': request.session.get('programme_name', 'Unknown')  # Using session
    }

    template = get_template('results_pdf.html')
    html_content = template.render(context)
    return generate_pdf(html_content)