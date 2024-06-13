from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
model_to_use = "gpt-4-turbo"

import time
import json

# List out 20 assistants defined in OpenAI and delete all assistants with name starting with demo
assistants = client.beta.assistants.list(
    order="desc",
    limit="20",
)

# delete all assistants with name starting with demo
for i in range(len(assistants.data)):
  print(assistants.data[i].name)
  if assistants.data[i].name.startswith("demo"):
    client.beta.assistants.delete(assistants.data[i].id)

custom_tools = [
    {
        "type":"function",
        "function": {
            "name":"redirect_assistant",
            "description":"redirecting to a professional of a subject",
            "parameters": {
                "type":"object",
                "properties": {
                    "assistant_name": {
                        "type":"string",
                        "description":"the professional name to redirect to.  choices are 'math' or 'history'"
                    }
                }
            }
        }
    }
]


general_assistant = client.beta.assistants.create(
    instructions = """
      You are a general teacher that will give a short sentence as the answer.
      However, if the question is about math or history, you should use the redirect tool
      to redirect the topic to a professional for further answer.
    """,
    name="demoGeneralTeacher",
    tools=custom_tools,
    model=model_to_use
)
print("general_assistant_id:" + general_assistant.id)

#default assistant is general
current_assistant_id = general_assistant.id

history_assistant = client.beta.assistants.create(
    instructions = """
      You are a history professional, you will give detail answers to the student.
      You will begin you answer with "Long Long Time Ago..."
    """,
    name="demoHistoryTeacher",
    tools=[],
    model=model_to_use
)
print("history_assistant id:" + history_assistant.id)
math_assistant = client.beta.assistants.create(
    instructions = """
      You are a math professional, you will give detail answers to the student.
      You will begin you answer with "In The World Of Numbers..."
    """,
    name="demoMathTeacher",
    tools=[],
    model=model_to_use
)
print("math_assistant id:" + math_assistant.id)

thread = client.beta.threads.create()
message1 = client.beta.threads.messages.create(
    thread.id,
    role="user",
    # content="What happened in world war 2?"
    content="What is a prime number?"
)
print(thread)
print(message1)
run = client.beta.threads.runs.create(
    thread_id = thread.id,
    assistant_id = general_assistant.id
)

# python function to change assistant
def redirect_assistant(assistant_name):
  global current_assistant_id
  print("Redirecting to " + assistant_name)
  if assistant_name in ["history", "math"]:
    if assistant_name == 'math':
      current_assistant_id = math_assistant.id
    else:
      current_assistant_id = history_assistant.id

    print("changing assistant id to:" + current_assistant_id)
    return "refering to " + assistant_name + " for further explanation"
  else:
    return "no specialist assistant here.  Keep it general."

# wait for run to complete. For runs expecting to complete without function call
# def wait_for_run(run_to_wait):
#   run_wait = client.beta.threads.runs.retrieve(
#     thread_id=thread.id,
#     run_id = run_to_wait.id
#   )

#   while not (run_wait.status == "completed"):
#     run_wait = client.beta.threads.runs.retrieve(
#       thread_id=thread.id,
#       run_id = run_to_wait.id
#     )
#     print("Waiting to complete:" + run_wait.status)
#     time.sleep(1)
def wait_for_run(run_to_wait):
  while True:
    run_wait = client.beta.threads.runs.retrieve(
      thread_id=thread.id,
      run_id = run_to_wait.id
    )
    if run_wait.status == "completed":
      break
    print("Waiting to complete:" + run_wait.status)
    time.sleep(1)
    
    
# function to print the current messages in the thread
def print_messages(messages):
  for i in range(len(messages)):
    print(messages[i].content[0].text.value)

# submit function call result, so the flow can continue
def submit_tool_call_output(run_id, tool_call_id, function_name, function_parameters):
    print("tool_call_id " + tool_call_id)
    print("function_name " + function_name)
    print("function_parameters " + function_parameters)

    function_call_result = ""
    if function_name == "redirect_assistant":
      parameter_obj = json.loads(function_parameters)
      print(parameter_obj)
      function_call_result = redirect_assistant(parameter_obj['assistant_name'])
      print("function call result:" + function_call_result)


    run_tool_submit = client.beta.threads.runs.submit_tool_outputs(
      thread_id=thread.id,
      run_id=run_id,
      tool_outputs=[
        {
          "tool_call_id": tool_call_id,
          "output": function_call_result
        }
      ]
    )
    wait_for_run(run_tool_submit)


# wait for 5s for the process to complete
for i in range(5):
  run = client.beta.threads.runs.retrieve(
    thread_id=thread.id,
    run_id = run.id
  )
  # function call happened, requiring action from the server side (not open ai) to complete, and submit the result
  if run.status == "requires_action":
    # getting the first call, can have multiple actions
    first_tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
    tool_call_id = first_tool_call.id
    function_name = first_tool_call.function.name
    function_parameters = first_tool_call.function.arguments

    # first by calling the python function, and submit the result back to open ai
    submit_tool_call_output(run.id, tool_call_id, function_name, function_parameters)

  # after submitting the result of tool call, the run would continue, and finally reach completed
  if run.status == "completed":
    print(run)
    messages = client.beta.threads.messages.list(
      thread_id=thread.id
    )
    print(messages)
    print_messages(messages.data)

    break
    # print(first_tool_call)
  time.sleep(1)

# submit a message on behalf of user, and ask for more detail.  The current assistant should now be either history or math, or still for general
message = client.beta.threads.messages.create(
    thread.id,
    role="user",
    content="Please give me more details"
)
print("answering by current_assistant_id:" + current_assistant_id)
run = client.beta.threads.runs.create(
    thread_id = thread.id,
    assistant_id = current_assistant_id
)
wait_for_run(run)
messages = client.beta.threads.messages.list(
  thread_id=thread.id
)
print_messages(messages.data)
