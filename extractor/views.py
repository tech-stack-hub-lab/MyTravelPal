from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from httpcore import request

from .models import UploadedDocument
from .utils import extract_text
from .llm import ask_document, travel_assistant
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.core.paginator import Paginator

DOCUMENT_TEXT = ""



def upload_file(request):

    global DOCUMENT_TEXT

    extracted_text = ""
    answer = ""

    booking_details = {}

    uploads = UploadedDocument.objects.order_by(
    "-created_at"
    )
    paginator = Paginator(
    uploads,
    5
    )
    page_number = request.GET.get(
    "page"
    )
    uploads = paginator.get_page(
    page_number
    )

    if request.method == "POST":

        # ----------------------------------------------------
        # 1. PASTE EMAIL / BOOKING TEXT
        # ----------------------------------------------------
        if "extract_text" in request.POST:

            booking_text = request.POST.get(
                "booking_text",
                ""
            )

            extracted_text = booking_text

            DOCUMENT_TEXT = booking_text

            prompt = f"""
            Extract:

            - Hotel Name
            - Hotel Location
            - Check-In Date
            - Check-Out Date
            - Flight Number
            - Airline
            - Booking Reference

            Text:

            {booking_text}
            """

            answer = travel_assistant(prompt)

            booking_details = {
                "raw_text": booking_text
            }

        # ----------------------------------------------------
        # 2. FILE UPLOAD
        # ----------------------------------------------------
        elif "upload_file" in request.POST:

            if "file" in request.FILES:

                uploaded_file = request.FILES["file"]

                fs = FileSystemStorage()

                filename = fs.save(
                    uploaded_file.name,
                    uploaded_file
                )

                file_path = fs.path(filename)

                extracted_text = extract_text(
                    file_path
                )

                DOCUMENT_TEXT = extracted_text

                UploadedDocument.objects.create(

                    filename=uploaded_file.name,

                    extracted_text=extracted_text

                )

                answer = travel_assistant(
                    f"""
                    Extract travel related
                    booking information:

                    {extracted_text}
                    """
                )

        # ----------------------------------------------------
        # 3. AI CHAT ASSISTANT
        # ----------------------------------------------------
        elif "ask_assistant" in request.POST:

            question = request.POST.get(
                "question",
                ""
            )

            if DOCUMENT_TEXT:

                answer = ask_document(
                    DOCUMENT_TEXT,
                    question
                )

            else:

                answer = travel_assistant(
                    question
                )

        # ----------------------------------------------------
        # 4. SAVE TO TRIP
        # ----------------------------------------------------
        elif "save_trip" in request.POST:

            messages.success(
                request,
                "Trip saved successfully."
            )

    return render(
        request,
        "upload.html",
        {
            "answer": answer,
            "text": extracted_text,
            "uploads": uploads,
            "booking": booking_details,
        }
    )
def delete_upload(request,id):

    upload = get_object_or_404(
        UploadedDocument,
        id=id
    )

    upload.delete()

    return redirect("upload_file")
