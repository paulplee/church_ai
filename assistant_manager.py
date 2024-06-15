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
            


    def handle_function_call(self, function_name, params):
        
        function_call_result = ""
        if function_name == 'redirect_assistant':
        # Create a new assistant or modify the prompt
        #     print(f"========{function_name}: {params}========")
        #     if params == 'travel':
        #         self.assistant = self.assistants["alpha_Travel_Agent"]
            
        # elif function_name == 'ask_again':
        #     print(f"========{function_name}: {params}========")
            function_call_result = self.redirect_assistant(params)
            print(f"========function call result: {function_call_result}========")
        run_tool_submit = client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=[
                {
                "tool_call_id": self.run.required_action.submit_tool_outputs.tool_calls[0].id,
                "output": function_call_result
                }
            ]
        )
        self.wait_for_run(run_tool_submit)


    def wait_for_run(self, run_to_wait):
        while True:
            run_wait = client.beta.threads.runs.retrieve(
                thread_id= self.thread.id,
                run_id = run_to_wait.id
            )
            if run_wait.status == "completed":
                messages = client.beta.threads.messages.list(
                thread_id=self.thread.id
                )
                for i in range(len(messages.data)):
                    print(messages.data[i].content[0].text.value)
                break
            print("Waiting to complete:" + run_wait.status)
            time.sleep(1)


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
        print(f"Assistant created: {assistant_obj.id}")
    
    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"========create_thread()========")
            print(f"Thread created: {self.thread.id}")
            
    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )
            # print(f"========add_message_to_thread()========")

    
    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions
            )
            # print(f"========run_assistant()========")

            
    def process_messages(self):
        print(f"========process_messages()========")
        print("THREAD: ", self.thread)
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            print(f"MESSAGES: {messages}")
            summary = []
            
            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)
            
            self.summary = "\n".join(summary)
            print(f"SUMMARY ----> {role.capitalize()}: {response}")
    
            # for message in messages:
            #     role = message.role
            #     content = message.content[0].text.value
            #     print(f"SUMMARY ----> {role.capitalize()}: {content}")

    def call_required_function(self, required_actions):
        print(f"========call_required_function()========")
        if not self.run:
            return
        tool_outputs = []
        for action in required_actions["tool_calls"]:
            print(f"***REQUIRED ACTION: {action}")
            function_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])
            print(f"***FUNCTION NAME: {function_name}")
            
            if function_name == "redirect_assistant":
                # output = self.handle_function_call(function_name=function_name, params=arguments["assistant_name"])
                # print(f"OUTPUT: {output}")
                # final_str = ""
                # if output:
                #     for item in output:
                #         final_str += "".join(item)
                # tool_outputs.append({"tool_call_id": action["id"], "output": final_str})
                self.redirect_assistant(arguments["assistant_name"])
                run_tool_submit = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread.id,
                    run_id=self.run.id,
                    tool_outputs=[
                        {
                        "tool_call_id": action["id"],
                        "output": "output"
                        }
                    ]
                )
                self.wait_for_run(run_tool_submit)
                            
            else:
                raise ValueError(f"Invalid function name: {function_name}")
        print("Submitting outputs back to the Assistant...")
        # self.client.beta.threads.runs.submit_tool_outputs(
        #     thread_id=self.thread.id,
        #     run_id=self.run.id,
        #     tool_outputs=tool_outputs
        # )

    # For Streamlit
    def get_summary(self):
        print(f"========get_summary()========")
        print("SUMMARY: ", self.summary)
        return self.summary
        
    def wait_for_completion(self):
        print(f"========wait_for_completion()========")
        if self.thread and self.run:
            while True:
                time.sleep(1)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id
                )
                # print(f"RUN STATUS: {run_status.model_dump_json(indent=4)}")
                
                if run_status.status == "completed":
                    print(f"\nRun Status is COMPLETED\n")
                    self.process_messages()
                    break
                elif run_status.status == "requires_action":
                    print(f"\nRun Status is REQUIRES_ACTION\n")
                    
                    # getting the first call, can have multiple actions
                    required_action = run_status.required_action
                    print(f"Required Action: {required_action}")
                    type = required_action.type
                    print(f"Required Action Type: {type}")
                    first_tool_call = run_status.required_action.submit_tool_outputs.tool_calls[0]
                    tool_call_id = first_tool_call.id
                    function_name = first_tool_call.function.name
                    function_parameters = first_tool_call.function.arguments

                    results=self.call_required_function(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )
                    return results


    # Get back a log of all the steps executed by the assistant
    def run_steps(self):
        print(f"========run_steps()========")
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id,
            run_id=self.run.id    
        )
        print(f"Run-Steps:: {run_steps}")
        return run_steps.data
