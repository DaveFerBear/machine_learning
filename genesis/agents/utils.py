import os
import mimetypes
import requests
from dotenv import load_dotenv
from ollama import chat
import base64

def encode_image(image_path):
    """Encode image to base64 format"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def inference_with_api(image_path, prompt, model_id="qwen3-vl:4b"):
    """
    API-based inference using a local Ollama model.

    Args:
        image_path (str): Path to the image file on disk.
        prompt (str): Text prompt to send along with the image.
        model_id (str): Name of the Ollama model to use (e.g. 'qwen2.5-vl', 'llava', etc.)

    Returns:
        str: The assistant's text response.
    """
    print("Using model: ", model_id)
    # For Ollama, you don't need to base64-encode the image;
    # you pass the file path via the 'images' field.
    messages = [
        {
            "role": "user",
            "content": prompt,
            "images": image_path if isinstance(image_path, list) else [image_path]
        }
    ]

    response = chat(model=model_id, messages=messages)

    # Handle both attribute-style and dict-style access just in case
    try:
        return response.message.content
    except AttributeError:
        return response["message"]["content"]



def inference_with_api_gemini(image_path, prompt, model_id="gemini-3"):
    base64_image = encode_image(image_path)

    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/png"  # fallback

    api_key = os.environ["GEMINI_API_KEY"]
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_id}:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_image,
                        }
                    },
                ]
            }
        ]
    }

    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]