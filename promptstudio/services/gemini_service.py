from core.config import settings
from google import genai
from google.genai import types


class GeminiService:

    def __init__(self, llm_config):
        
        self.gemini_cred = settings.GEMINI_CREDENTIALS
        self.PROJECT_ID = settings.GOOGLE_GEMINI_PROJECT_ID
        self.REGION = settings.GOOGLE_GEMINI_REGION  
        # Update LLM config
        self.llm_config = llm_config
    
    def generate_response(self, prompt,
                          context,
                          system_message,
                          examples: list[dict[str, str]],
                          no_chunk_gemini_doc_items,
                          is_google_search = False):

        client = genai.Client(vertexai=True, 
                              project=self.PROJECT_ID, 
                              location=self.REGION, 
                              credentials=self.gemini_cred)
        
        docs_bytes = [types.Part.from_bytes(data = item['data'], mime_type = item['docType']) for item in no_chunk_gemini_doc_items]
        content_list = []
        # Filter for google search
        if not is_google_search:
            examples = [dict(example) for example in examples]
            for example in examples:
                content_list.append(types.Content(role = "user",
                                                parts = [types.Part.from_text(text=example["question"])]))
                content_list.append(types.Content(role = "model",
                                                parts = [types.Part.from_text(text=example["response"])]))
        
            if context:
                content_list.append(context)
            if docs_bytes:
                for i in range(len(docs_bytes)):
                    content_list.append(docs_bytes[i])
                    
        gemini_config_dict = {'system_instruction' : system_message,
                              'temperature': self.llm_config['temperature'],
                              "top_p": self.llm_config['topProbabilities'],
                              "max_output_tokens" : self.llm_config['maxResponseLength']
                              }
        if is_google_search:
            gemini_config_dict["tools"] = [{'google_search_retrieval': types.GoogleSearchRetrieval()}]
        content_list.append(prompt)
        response = client.models.generate_content(
            model = settings.GOOGLE_GEMINI_MODEL,
            contents=content_list,
            config= gemini_config_dict
        )
        return response.text
    