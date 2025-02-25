# backend/app/modules/conversation/conversation_service.py
from typing import Dict
from .llm_client import call_llm


class ConversationService:
    def __init__(self, call_llm: call_llm):
        self.llm_call = call_llm

    def process_query(self, user_query: str, problem_id: int) -> str:
        print(f"Processing query: {user_query}")
        print(f"Problem ID: {problem_id}, type: {type(problem_id)}")
        metadata = self.retrieve_problem_metadata(problem_id)
        prompt = self.build_augmented_prompt(metadata, user_query)
        print(f"generating a reponse for prompt: {prompt}")
        response = self.llm_call(prompt)
        return response
    
    def build_augmented_prompt(self, metadata: Dict, user_query: str):
        print(f"Building augmented prompt for user query: {user_query}")
        public_question = metadata.get("teacher_instructions", "")
        hidden_values = metadata.get("hidden_values", "")
        teacher_instructions = metadata.get("teacher_instructions", "")

        prompt = (
            f"You are here to faciliate a student in their learning/test environment. Adhere to the teachers settings while responding to the student."
            f"[Teacher Instructions: {teacher_instructions}]\n"
            f"[Public Question: {public_question}]\n"
            f"[Hidden Values: {hidden_values}]\n"
            f"Student Query: {user_query}\n"
            "AI:"
        )

        return prompt
    
    def retrieve_problem_metadata(self, problem_id: int) -> Dict:
        print (f"Retrieving metadata for problem_id: {problem_id}")
    ## dummy function to mock some query returnf
        return {
            "public_question": "what is x + y",
            "hidden_values": {"x": 3, "y": 10},
            "teacher_instructions": "Provide small hints unless directly asked for hidden values. Do not just solve the problem for the user."
        }
    
    def afterResponse(self, response: str, prompt: str, problem_id: int) -> str:
        '''
        This function is called after the response is generated. It will be used to log the response'''
        pass 
        

