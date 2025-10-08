from ..stores import VectorDBInterface,GenerationInterface,CHAT_SYSTEM_PROMPT,CHAT_USER_PROMPT



class AgMPentController:
    def __init__(self,vector_db:VectorDBInterface,generation:GenerationInterface,video_id:str):
        self.vector_db=vector_db
        self.generation=generation
        self.video_id=video_id
        self.MAX_CALLS=3 

    async def get_relevant_chunks(self, user_query: str, top_k: int=3):
        """Get relevant chunks from the vector database based on user query."""
        print(f"Searching for relevant chunks with query: {user_query} and top_k: {top_k} video_id: {self.video_id}")
        results = await self.vector_db.search(user_query=user_query, top_k=top_k, video_id=self.video_id)
        if not results or results.get("result") is None:
            return "No relevant chunks found."
        if not results.get("result") or len(results["result"]["hits"]) == 0:
            return "No relevant chunks found."
        
        preprocessed_results = [
            hit["fields"].get("text", "")
            for hit in results["result"]["hits"]
        ]
        return preprocessed_results
    


    async def get_model_answer(self, user_query: str, history: list = None, summary: str = '') -> str:
        """Generate an answer based on the user query and relevant chunks."""
        if history is None:
            history = []
        
        # Construct the message for the generation model
        user_prompt = CHAT_USER_PROMPT.format(user_query=user_query, history=history)
        system_prompt = CHAT_SYSTEM_PROMPT.format(video_summary=summary)
    
        message = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        calls = 0
        while calls < self.MAX_CALLS:
            calls += 1
            answer = await self.generation.generate_answer(message=message)
            
            # check if the answer is a function call
            if getattr(answer, "function_call", None):
                args = self.generation.get_tool_agrs(answer)
                
                if args:
                    tool_response = await self.get_relevant_chunks(
                        user_query=args.get("user_query", user_query), 
                        top_k=args.get("top_k", 3)
                    )
                    print(tool_response)
                    
                    # Build a new message including the tool response
                    tool_message = {
                        "role": "function",
                        "name": "get_relevant_chunks",
                        "content": str(tool_response)
                    }
                    message.append(tool_message)
                    # Continue the loop to get the final answer
                else:
                    # If args is None/empty, break to avoid infinite loop
                    break
            else:
                # Got a regular response, return it
                return answer.content
        
        # If we've exhausted MAX_CALLS, return the last answer content
        return getattr(answer, 'content', 'Unable to generate response after maximum attempts')


