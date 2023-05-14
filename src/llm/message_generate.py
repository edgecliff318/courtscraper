from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel

from src.core.config import get_settings

settings = get_settings()


llm = ChatOpenAI(temperature=0)

prompt_with_context = PromptTemplate(
    input_variables=["instruction", "context"],
    template="{instruction}\n\nInput:\n{context}",
)


prompt_with_context = PromptTemplate(
    input_variables=["instruction", "context"],
    template="{instruction}\n\nInput:\n{context}",
)


class LLM(BaseModel):
    instruction: str
    context: str

    def predict(self):
        llm_context_chain = LLMChain(llm=llm, prompt=prompt_with_context)
        return llm_context_chain.predict(
            instruction=self.instruction, context=self.context
        ).lstrip()


if __name__ == "__main__":
    # context = """George Washington (February 22, 1732[b] – December 14, 1799) was an American military officer, statesman, and Founding Father who served as the first president of the United States from 1789 to 1797."""
    # response = LLM(instruction="When was George Washington president?", context=context).predict()
    # print('response: ', response)

    context = """
You work as an assistant to a lawyer in the USA,\
and your role is to generate messages that the lawyer can send to clients. These messages should include a \
copy of the case, along with the date, type, and status of the case, as well as any relevant message about the case
information of case of client.\
`['Case ID', 'Date', 'First Name', 'Last Name' ,   'Charges']`
    """
    response = LLM(
        instruction="give message can send to cient", context=context
    ).predict()
    print("response: ", response)
