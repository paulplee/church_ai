import openai
from dotenv import load_dotenv

def cleanup_assistants():
    load_dotenv()
    client = openai.OpenAI()

    # List all assistants
    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        if "alpha_" in assistant.name or "alpha_" in assistant.name:
            print(f"XXX DELETING: Assistant ID: {assistant.id}, Name: {assistant.name}")
            client.beta.assistants.delete(assistant.id)
            assistants.data.remove(assistant)

    print("+++ REMAINING ASSISTANTS +++")
    for assistant in assistants.data:
        print(f"Assistant ID: {assistant.id}, Name: {assistant.name}")

