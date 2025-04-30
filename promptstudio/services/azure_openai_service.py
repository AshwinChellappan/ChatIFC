import openai
from openai import AzureOpenAI
import requests
from core.config import settings
import json
import time
from util.logger import Logger

logger = Logger()

class AzureOpenAIService:

    def __init__(self, llm_config):
        # Update LLM config
        self.llm_config = llm_config
        # API base
        self.api_base = settings.AZURE_OPENAI_BASE_PATH
        # API key
        self.api_key = settings.AZURE_OPENAI_API_KEY
        # API version
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        # 
        self.base_url = f"{self.api_base}openai/deployments/{self.llm_config['llmModel']}/chat/completions?api-version={self.api_version}"

    def generate_embeddings(self, text):
        client = AzureOpenAI(
            api_key = self.api_key,  
            api_version = self.api_version,
            azure_endpoint = self.api_base
        )
        # Get response
        embedding_response = client.embeddings.create(
            input = text,
            model= "text-embedding-ada-002"  # model = "deployment_name".
        )
        # Get str response
        str_response = embedding_response.model_dump_json(indent=2)
        # Get dict response
        dict_response = json.loads(str_response)
        # Get embeddings
        embeddings = dict_response['data'][0]['embedding']
    
        return embeddings

    def generate_response(self, prompt, context,system_message, examples: list[dict[str, str]]):
        """
        Generate a response from Azure OpenAI GPT-3.5 model.

        Parameters:
        - prompt (str): The prompt to send to the model.
        - context (str): The context to provide additional information for the model.
        - api_key (str): Your Azure OpenAI API key.
        - endpoint (str): The endpoint URL for your Azure OpenAI service.

        Returns:
        - str: The generated response from the model.
        """
        
        # Headers for the API request
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key,
        }
        
        messages = [{"role": "system", "content": system_message}]
                        # Add few-shot examples to the messages
        
        examples = [dict(example) for example in examples]

        for example in examples:
            messages.append({"role": "user", "content": example["question"]})
            messages.append({"role": "assistant", "content": example["response"]})

        context_and_prompt = context + '\n ### \n' + prompt
        messages.append({"role": "user", "content": context_and_prompt})            
        # Payload for the API request
        payload = {
            "messages": messages,
            "temperature": self.llm_config['temperature'],  # Adjust the temperature value as desired
            "top_p": self.llm_config['topProbabilities'], # Adjust the top P value as desired
            "max_tokens": self.llm_config['maxResponseLength'],  # Adjust the maximum response length as desired
            "stop": None  # You can specify a stop sequence to control the response termination
        }
        # success identifier
        response_obtained = False
        prompt_response = ''
        time_to_wait = 0
        retries = 3     
        while not response_obtained:
            response = requests.post(self.base_url, headers = headers, json = payload)
            if response.status_code == 429:
                error_dict = response.json()
                error_msg = error_dict['error']['message']
                time_to_wait = self.extract_time_to_wait(error_msg)
                if retries > 0:
                    # Sleep
                    logger.log(f'Per minute token limit reached. Retrying after {time_to_wait}s.')
                    time.sleep(time_to_wait)
                    retries -= 1
                    continue
                else:
                    prompt_response = f"There was an error generating the response. Error: {response.status_code}, {response.text}"
                    response_obtained = True  
            elif response.status_code == 200:
                response_data = response.json()
                prompt_response = response_data['choices'][0]['message']['content']
                response_obtained = True
            else:
                prompt_response = f"There was an error generating the response. Error: {response.status_code}, {response.text}"
                response_obtained = True
       
        return prompt_response

    def extract_time_to_wait(self, error_msg):
        # Default time to wait
        time_to_wait = 5
        try:
            # Split the error message 
            error_sentences = error_msg.split('.')
            # Get the time sentence
            time_sentence = [error_sentence for error_sentence in error_sentences if 'retry' in error_sentence.lower()]
            # Extract time to wait
            time_to_wait = int(time_sentence[0].split(' ')[-2])
        except Exception as error:
            logger.log("Time to wait couldn't be extracted")

        return time_to_wait