import time
import pandas as pd
import os

from langchain_groq import ChatGroq
from app.config import get_groq_model

from .prompts import QUESTION_GENERATION_PROMPT

llm = ChatGroq(
    model=get_groq_model(),
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_question(context: str):

    prompt = QUESTION_GENERATION_PROMPT.format(
        context=context
    )

    response = llm.invoke(prompt)

    return response.content.strip()


def generate_qa_dataset(
    docs,
    output_file,
):

    rows = []

    for doc in docs:

        question = generate_question(
            doc.page_content
        )

        rows.append(

            {

                "question": question,

                "answer": doc.page_content,

                "role": doc.metadata.get(
                    "role",
                    ""
                ),

                "source": doc.metadata.get(
                    "source",
                    ""
                )

            }

        )

        time.sleep(1)

    df = pd.DataFrame(rows)

    df.to_csv(
        output_file,
        index=False
    )

    return df
