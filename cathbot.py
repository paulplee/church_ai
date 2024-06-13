# Required pakages:
# ================
# python-dotenv
# openai
# requests
# streamlit

import streamlit as st
from session_state import SessionState
import pandas as pd
from assistant_manager import AssistantManager
from assistant_templates import Crew
from utils import cleanup_assistants
        
def dict_to_df(d):
    return pd.DataFrame(list(d.items()), columns=['Name', 'Value'])

def get_function_name(item_dict):
    tool_calls = item_dict.get('step_details', {}).get('tool_calls', [])
    for call in tool_calls:
        function = call.get('function', {})
        name = function.get('name')
        if name:
            return name
    return None
        
def main():
    cleanup_assistants()
    
    # 5treamlit interface
    
    st.title("Cathbot")
    current_step = st.empty()

    state = SessionState.get(manager=None)
            
            
    if state.manager is None:
        state.manager = AssistantManager()

        print("CREW: ", len(Crew))
        for template in Crew:
            print(f"== Creating Assistant: {template.name}")
            state.manager.create_assistant(
                assistant_template = template                
            ) 

        # for name, assistant in AssistantManager.assistants.items():
        #     print(f"Assistant name: {name}, ID: {assistant.id}")

    state.manager.assistant = AssistantManager.assistants["alpha_Greeter"]

    current_step.text("create_thread()")
    state.manager.create_thread()
    current_step.text("Waiting for user input...")
    
    with st.form(key="user_input_form"):
        instructions = st.text_input("Enter topic")
        submit_button = st.form_submit_button(label="Ask Cathbot")
        
        if submit_button:
            
            current_step.text("add_message_to_thread()")
            state.manager.add_message_to_thread(
                role = "user",
                content=f"{instructions}")
            
            current_step.text("run_assistant()")            
            state.manager.run_assistant(instructions = "Help the user find the right insurance plan")
            
            current_step.text("Waiting for completion...")
            state.manager.wait_for_completion()
            summary = state.manager.get_summary()
            st.write(summary)
            st.text("Run Steps:")
            # st.code(manager.run_steps(), line_numbers=True, language='md')

            output = state.manager.run_steps()
            for item in output:
                print(f"ITEM: {item}")
                item_dict = item.model_dump()
                function_name = get_function_name(item_dict)
                df = dict_to_df(item_dict)
                st.table(df)
                if function_name:
                    current_step.text(f"Function called: {function_name}")


if __name__ == "__main__":
    main()
