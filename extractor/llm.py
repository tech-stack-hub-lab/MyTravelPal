import ollama

def ask_document(
    document,
    question
):

    prompt = f"""
    Document:

    {document}

    Question:

    {question}
    """

    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response["message"]["content"]

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

    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response["message"]["content"]