# Simple Streamlit/Bedrock/Anthropic Claude 3 text generation example
# Author: Gary A. Stafford
# Date: 2024-08-22

import datetime
import json
import logging

import boto3
import streamlit as st
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def setup_bedrock_client():
    """Setup the Bedrock client."""
    return boto3.client(service_name="bedrock-runtime")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def create_request_body(
    max_tokens, temperature, top_p, top_k, system_prompt, user_prompt, assistant_prompt
):
    """Create the request body for the Bedrock API.
    Args:
        max_tokens (int): Maximum number of tokens to generate.
        temperature (float): Temperature for sampling.
        top_p (float): Top P sampling.
        top_k (int): Top K sampling.
        system_prompt (str): System prompt.
        user_prompt (str): User prompt.
        assistant_prompt (str): Assistant prompt.
    Returns:
        str: JSON request body.
    """
    user_message = {
        "role": "user",
        "content": user_prompt,
    }
    messages = [user_message]

    if assistant_prompt:
        assistant_message = {
            "role": "assistant",
            "content": assistant_prompt,
        }
        messages.append(assistant_message)

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "system": system_prompt,
            "messages": messages,
        }
    )
    logger.info(json.dumps(json.loads(body), indent=4))

    return body


def invoke_bedrock(bedrock_runtime, model_id, body):
    """Invoke the Bedrock model.
    Args:
        bedrock_runtime (boto3.client): Bedrock runtime client.
        model_id (str): Bedrock model ID.
        body (str): JSON request body.
    Returns:
        dict: JSON response body.
    """
    try:
        response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
        response_body = json.loads(response.get("body").read())
        logger.info(json.dumps(response_body, indent=4))
        return response_body
    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        st.error(f"A client error occurred: {message}")
        return None


def display_response(response, analysis_time):
    """Display the response from the model.
    Args:
        response (dict): JSON response body.
        analysis_time (float): Time to analyze the response.
    Returns:
        None
    """
    st.text_area(
        height=500,
        label="Model response",
        value=response.get("content")[0].get("text"),
    )

    input_tokens = f"Input tokens: {response.get('usage').get('input_tokens')}"
    output_tokens = f"Output tokens: {response.get('usage').get('output_tokens')}"
    analysis_time_str = f"Response time: {analysis_time:.2f} seconds"
    stats = f"{input_tokens}  |  {output_tokens} |  {analysis_time_str}"
    st.text(stats)


def main():
    st.set_page_config(page_title="Valorant ESports Assistant Manager", layout="wide")
    load_css("styles.css")

    hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
    </style>"""

    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    st.markdown("### Valorant ESports Assistant Manager")
    st.markdown(
        "The project is focused on building a VALORANT Assistant Manager using Streamlit and Amazon Bedrock to assist with team management by leveraging The project is focused on building a VALORANT Assistant Manager using Streamlit and Amazon Bedrock to assist with team management by leveraging LLM's (for our case, Claude v2)."
    )

    with st.form("my_form"):
        st.markdown("###### Prompts")
        system_prompt = st.text_area(
            height=50,
            label="System (Optional)",
            value="You are an a manager for a professional VALORANT team. You have a busy schedule and need help managing your team. You are looking for a good roster that covers all bases.",
        )

        user_prompt = st.text_area(
            height=350,
            label="User (Required)",
            value="""I am struggling to manage my team and need help choosing what players work with certain maps and operators. Give me a proper roster that covers all bases.

Consider all of the following requirements:

<requirements>
    - Player Roles & Agent Specialization
    - Team Synergy & Communication
    - Adaptability & Meta Awareness
    - Mechanical Skill & Game Sense
    - Map Knowledge & Strategy
    - Statistics & Performance Metrics
</requirements>

Think step-by-step before you choose the roster.
""",
        )

        assistant_prompt = st.text_area(
            height=50,
            label="Assistant (Optional)",
            value="",
        )

        st.divider()
        st.markdown("###### Model")

        model_id = st.selectbox(
            "Model ID",
            options=[
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-3-haiku-20240307-v1:0",
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-3-opus-20240229-v1:0",
            ],
            index=0,
        )

        st.divider()
        st.markdown("###### Parameters")

        row1 = st.columns([2, 2])
        max_tokens = row1[0].slider(
            "Max Tokens (Depends on model)",
            min_value=1,
            max_value=8192,
            value=1000,
            step=1,
        )
        temperature = row1[1].slider(
            "Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1
        )

        row2 = st.columns([2, 2])
        top_p = row2[0].slider(
            "Top P", min_value=0.0, max_value=1.0, value=0.99, step=0.01
        )
        top_k = row2[1].slider("Top K", min_value=1, max_value=500, value=250, step=1)

        st.divider()

        submitted = st.form_submit_button("Submit")

        if submitted and user_prompt:
            with st.spinner():
                start_time = datetime.datetime.now()
                bedrock_runtime = setup_bedrock_client()
                body = create_request_body(
                    max_tokens,
                    temperature,
                    top_p,
                    top_k,
                    system_prompt,
                    user_prompt,
                    assistant_prompt,
                )
                response = invoke_bedrock(bedrock_runtime, model_id, body)
                end_time = datetime.datetime.now()
                analysis_time = (end_time - start_time).total_seconds()
                if response:
                    display_response(response, analysis_time)
                else:
                    logger.error("Failed to get a valid response from the model.")
                    st.error("Failed to get a valid response from the model.")


if __name__ == "__main__":
    main()
