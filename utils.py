import openai
from dotenv import load_dotenv

def cleanup_assistants():
    load_dotenv()
    client = openai.OpenAI()

    # List all assistants
    assistants = client.beta.assistants.list(limit=100)
    for assistant in assistants.data:
        if "demo" in assistant.name or "cathbot_" in assistant.name:
            try:            
                print(f"XXX DELETING: Assistant ID: {assistant.id}, Name: {assistant.name}")
                client.beta.assistants.delete(assistant.id)
                assistants.data.remove(assistant)
            except:
                print(f"XXX FAILED TO DELETE: Assistant ID: {assistant.id}, Name: {assistant.name}")

    print("+++ REMAINING ASSISTANTS +++")
    for assistant in assistants.data:
        print(f"Assistant ID: {assistant.id}, Name: {assistant.name}")

if __name__ == "__main__":
    cleanup_assistants()