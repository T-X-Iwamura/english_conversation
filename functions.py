import streamlit as st
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from langchain.chains import ConversationChain

def create_chain(system_template, llm, memory):
    """
    LLMによる回答生成用のChain作成
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_template),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    chain = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt
    )

    return chain


def create_evaluation():
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")

    return llm_response_evaluation