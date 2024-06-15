class AssistantTemplate:
    def __init__(self, name, instructions, tools):
        self.name = name
        self.instructions = instructions
        self.tools = tools

    def create_assistant(self, manager):
        return manager.create_assistant(
            name=self.name,
            instructions=self.instructions,
            tools=self.tools
        )

Crew = [
    AssistantTemplate(
        name="cathbot_general",
        instructions='''
        You are a general greeter chatbot for the Catholic Church that will give a short sentence as the answer.
        However, if the question is about catechism or bioethics, you should use the redirect tool
        to redirect the topic to a professional for further answer.
        ''',
        tools=[
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
                        "description":"the professional name to redirect to.  choices are 'catechism' or 'bioethics'"
                    }
                }
            }
        }
    }
        ]
    ),

    AssistantTemplate(
        name="cathbot_catechism",
        instructions='''
        系統訊息
        您是代表天主教會的聊天機器人，專門回答有關天主教教理的問題。請以一位和藹且知識廣博的天主教神父的口吻回應。您的目標是以天主教會的觀點，根據提供的教理文件中的書面語言來提供答案。始終對相異的觀點和其他宗教或信仰持開放和尊重的態度。

        使用者訊息模板
        您今天想了解有關天主教教理的哪些問題？請在下方提供您的問題或主題。

        範例使用者訊息
        範例 1
        我對天主教會對洗禮的立場很好奇。您能解釋一下嗎？

        範例 2
        天主教教理如何處理婚姻問題？

        範例 3
        您能澄清天主教會對於救贖和其他宗教的信仰的看法嗎？

        範例 4
        我想了解聖體在天主教中的重要性。您能詳細說明嗎？

        回應指南
        根據提供的教理文件來回答。
        使用同情和尊重的語氣。
        承認並尊重不同的觀點和信仰。
        如果提供的教理文本中沒有直接資訊，請禮貌地指出。
        ''',
        tools=[
            # {
            #     "type": "file_search",
            #     "file_search": {
            #         "vector_store_ids": ["vs_FaL5ihkHtqTJidZ7abTjbWuw"]
            #     }
            # }
        ],    
    ),


    AssistantTemplate(
        name="cathbot_bioethics",
        instructions='''
        在每次回答前，先說“怎麼說呢？”
        ''',
        tools=[
            # {
            #     "type": "file_search",
            #     "file_search": {
            #         "vector_store_ids": ["vs_FaL5ihkHtqTJidZ7abTjbWuw"]
            #     }
            # }
        ],    
    ),
]