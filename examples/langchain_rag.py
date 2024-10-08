from indexify_langchain import IndexifyRetriever

# init client
client = IndexifyClient.create_namespace("test-langchain")
client.add_extraction_policy(
    "tensorlake/minilm-l6",
    "minilml6",
)

# Add Documents
client.add_documents("Lucas is from Atlanta Georgia")

# Initialize retriever
params = {"name": "minilml6.embedding", "top_k": 9}
retriever = IndexifyRetriever(client=client, params=params)

# Setup Chat Prompt Template
from langchain.prompts import ChatPromptTemplate

template = """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Use three sentences maximum and keep the answer concise.
Question: {question} 
Context: {context} 
Answer:
"""
prompt = ChatPromptTemplate.from_template(template)

# Ask llm question with retriever context
from langchain_openai import ChatOpenAI

from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Ask LLM Question
query = "Where is Lucas from?"
print(rag_chain.invoke(query))
