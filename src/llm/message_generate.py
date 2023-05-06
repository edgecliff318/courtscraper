from langchain import PromptTemplate, LLMChain
from langchain.llms import HuggingFacePipeline
from langchain.llms import HuggingFaceHub, OpenAI


from transformers import pipeline

import torch

from pydantic import BaseModel
import os

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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" # TODO: replace here
# os.environ["OPENAI_API_KEY"] = ""


# generate_text = pipeline(
#     model="databricks/dolly-v2-3b",
#     torch_dtype=torch.bfloat16,
#     trust_remote_code=True,
#     device_map="auto",
#     return_full_text=True
# )
# llm = HuggingFacePipeline(pipeline=generate_text)


repo_id = "databricks/dolly-v2-12b"
# repo_id = "google/flan-ul2"   
repo_id = "StabilityAI/stablelm-tuned-alpha-7b"
llm = HuggingFaceHub(repo_id=repo_id, model_kwargs={"temperature":0.1, "max_new_tokens":250})
# llm = OpenAI(temperature=0)

prompt_with_context = PromptTemplate(
    input_variables=["instruction", "context"],
    template="{instruction}\n\nInput:\n{context}"
)




prompt_with_context = PromptTemplate(
    input_variables=["instruction", "context"],
    template="{instruction}\n\nInput:\n{context}"
)


class LLM(BaseModel):
    instruction: str
    context: str
    
    def predict(self):
        llm_context_chain = LLMChain(llm=llm, prompt=prompt_with_context)
        return llm_context_chain.predict(instruction=self.instruction, context=self.context).lstrip()

if __name__ == "__main__":
    # context = """George Washington (February 22, 1732[b] – December 14, 1799) was an American military officer, statesman, and Founding Father who served as the first president of the United States from 1789 to 1797."""
    # response = LLM(instruction="When was George Washington president?", context=context).predict()
    # print('response: ', response)
    
    context = """
You work as an assistant to a lawyer in the USA,\
and your role is to generate messages that the lawyer can send to clients. These messages should include a \
copy of the case, along with the date, type, and status of the case, as well as any relevant message about the case
information of case of client.\
``{{'Case ID': '[140484751](/case/140484751)', 'Date': '03/24/2023', 'First Name': 'MARK', 'Last Name': 'CURTIS', 'Phone': '(417) 466-6506', 'Email': 'No email addresses found', 'Status': 'not_contacted', 'Age': 60, 'Charges': 'Driving While Revoked Or Suspended \\r{\\xa0Ordinance\\xa0RSMo:\\xa0Not Available\\xa0}', 'Disposition': None}}``
    """
    response = LLM(instruction="give message can send to cient", context=context).predict()
    print('response: ', response)
    
