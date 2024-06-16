import os
import openai
from dotenv import load_dotenv

import time
import json

load_dotenv()

news_api_key = os.environ.get("NEWS_API_KEY")
client = openai.OpenAI()
model = "gpt-4-turbo"


class AssistantManager:
    assistant_id = None
    thread_id = None
    assistants = {}
    
    def __init__(self, model: str = model):
        print("===\n\nAssistantManager initialized\n\n===")
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None
    
        # Retrieve existing assistant and thread if IDs are ready
        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(assistant_id=AssistantManager.assistant_id)
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(thread_id=AssistantManager.thread_id)
            
    def create_assistant(self, assistant_template):
        # unique_tools = list(assistant_template.tools)
        assistant_obj = self.client.beta.assistants.create(
            name=assistant_template.name,
            instructions=assistant_template.instructions,
            tools=assistant_template.tools,
            model=self.model
        )
        AssistantManager.assistant_id = assistant_obj.id
        AssistantManager.assistants[assistant_template.name] = assistant_obj
    
    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            
    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )

    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions
            )

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(1)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id
                )
                
                if run_status.status == "completed":
                    self.process_messages()
                    break
                elif run_status.status == "requires_action":
                    # getting the first call, can have multiple actions
                    results=self.call_required_function(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )
                    return results

    def wait_for_run(self, run_to_wait):
        while True:
            run_wait = client.beta.threads.runs.retrieve(
                thread_id= self.thread.id,
                run_id = run_to_wait.id
            )
            if run_wait.status == "completed":
                print("Run completed:" + run_wait.status)
                break
            print("Waiting to complete:" + run_wait.status)
            time.sleep(1)



    def call_required_function(self, required_actions):
        if not self.run:
            return
        tool_outputs = []
        for action in required_actions["tool_calls"]:
            function_name = action["function"]["name"]
            tool_call_id = action["id"]
            # tool_call_id = required_actions.tool_calls[0].id
            arguments = json.loads(action["function"]["arguments"])
            if function_name == "redirect_assistant":
                output = self.redirect_assistant(arguments['assistant_name'])

                            
            else:
                raise ValueError(f"Invalid function name: {function_name}")

            run_tool_submit = client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread.id,
                run_id=self.run.id,
                tool_outputs=[
                    {
                        "tool_call_id": tool_call_id,
                        "output": output
                    }
                ]
            )
            self.wait_for_run(run_tool_submit)
            messages = client.beta.threads.messages.list(
                thread_id=self.thread.id
            )
            for i in range(len(messages.data)):
                print(messages.data[i].content[0].text.value)

            # submit a message on behalf of user, and ask for more detail.  The current assistant should now be either history or math, or still for general
            message = client.beta.threads.messages.create(
                self.thread.id,
                role="user",
                content="Please give me more details"
            )
            run = client.beta.threads.runs.create(
                thread_id = self.thread.id,
                assistant_id = self.assistant.id
            )
            self.wait_for_run(run)
            messages = client.beta.threads.messages.list(
            thread_id=self.thread.id
            )


            for i in range(len(messages.data)):
                print(messages.data[i].content[0].text.value)

    # python function to change assistant
    def redirect_assistant(self, assistant_name):
        print("Redirecting to " + assistant_name)
        if assistant_name in ["catechism", "bioethics"]:
            if assistant_name == 'catechism':
                self.assistant = self.assistants["cathbot_catechism"]
            else:
                self.assistant = self.assistants["cathbot_bioethics"]

            print("changing assistant to:" + self.assistant.name)
            return "refering to " + assistant_name + " for further explanation"
        else:
            return "no specialist assistant here.  Keep it general."
            
    def process_messages(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []
            
            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)
            
            self.summary = "\n".join(summary)
            print(f"SUMMARY ----> {role.capitalize()}: {response}")
    

    # For Streamlit
    def get_summary(self):
        print(f"========get_summary()========")
        print("SUMMARY: ", self.summary)
        return self.summary
        


    # Get back a log of all the steps executed by the assistant
    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id,
            run_id=self.run.id    
        )
        return run_steps.data
