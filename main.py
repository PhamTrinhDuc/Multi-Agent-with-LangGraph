from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from source.prompt import PROMPT_SYSTEM
from source.models import create_llm, create_embedder
from source.extract_specifications import extract_info
from source.vectorstore import ChromaQueryEngine
from source.config import AragProduct
from typing import Literal
import json



def save_history(question: str, response: str, user_id: str):
    body = [
        [
            {"role": "user", "content": question},
            {"role": "assistant", "content": response}
        ]
    ]
    with open(f"./history/{user_id}.json", 'a', encoding='utf-8') as f:
        json.dump(body, f, ensure_ascii=False, indent=4)



def load_history(user_id: str):
    try:
        with open(f"./history/{user_id}.json", 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)[:3][::-1]
                return history
            except json.JSONDecodeError:
                return []
    except FileNotFoundError:
        return []


def rewrite_history(query, llm, user_id: str):
    history = load_history(user_id=user_id)

    prompt = PROMPT_SYSTEM['rewite_query'].format(
        question=query,
        history=history if history else ''
    )

    print(f"Prompt: {prompt}")
    rewrited = llm.invoke(prompt)
    return rewrited.content



def respose_chatbot(df: pd.DataFrame, 
                    question: str, 
                    user_id: str,
                    llm_type: Literal['groq', 'openai']='openai', 
                    model_name: str = "gpt-4o-mini"): 

    llm = create_llm(llm_type=llm_type, 
                     model_name=model_name)
    history = load_history(user_id=user_id)

    query_rewrited = rewrite_history(query=question, llm=llm, user_id=user_id)
    print(f"Query rewrited: {query_rewrited}")

    embedder = create_embedder(embedder_type=llm_type)


    search_engine = ChromaQueryEngine(embedder=embedder, 
                                            df=df)
    demands =  extract_info(query_user=question, 
                                type_client=llm_type)
    context = search_engine.query( query=question, demands=demands)


    prompt =  PROMPT_SYSTEM['prompt_sys'].format(
        question=question,
        context=context,
        history=history if history else '',
    )
    response = llm.invoke(input=prompt)
    save_history(question=question, response=response.content, user_id=user_id)
    return response.content

def main():
    df = pd.read_csv(AragProduct.DATA_PATH)
    question = "Cho tôi xem sản phẩm số 2 đi ?"
    response = respose_chatbot(df=df, question=question, user_id="0962741764")
    print(response)

if __name__ == '__main__':
    main()    
