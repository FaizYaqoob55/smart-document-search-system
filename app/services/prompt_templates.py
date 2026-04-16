
def factual_prompt(context, query):
    return f"""
You are a helpful assistant.

Give a short and direct answer using ONLY the context.

Context:
{context}

Question:
{query}
"""


def summary_prompt(context, query):
    return f"""
Summarize the following in bullet points.

Context:
{context}

Question:
{query}
"""


def comparison_prompt(context, query):
    return f"""
Compare the concepts in a table format.

Context:
{context}

Question:
{query}
"""