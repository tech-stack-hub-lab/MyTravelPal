import ollama


def _fallback_response(message, error=None):
    if error:
        return (
            f"Unable to connect to Ollama right now. "
            f"{message}\n\n"
            f"Error: {error}"
        )
    return message


def ask_document(document, question):
    prompt = f"""
    Document:

    {document}

    Question:

    {question}
    """

    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return response["message"]["content"]
    except Exception as exc:
        return _fallback_response(
            f"I could not analyze the document automatically. Please review the extracted text manually.\n\nDocument: {document}\nQuestion: {question}",
            exc,
        )


def travel_assistant(question):
    prompt = f"""
    You are a travel guide.

    User Question:

    {question}

    Provide:

    - Recommendations
    - Travel Tips
    - Hotels
    - Restaurants
    - Nearby Attractions
    - Transport Advice
    """

    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return response["message"]["content"]
    except Exception as exc:
        return _fallback_response(
            f"I could not generate an AI travel response right now. Please review the uploaded booking details manually.\n\nQuestion: {question}",
            exc,
        )