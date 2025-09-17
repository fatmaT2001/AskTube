from ..stores import VectorDBInterface,GenerationInterface


SYSTEM_PROMPT = """
You are Ask-Tube, an AI study assistant that helps users learn from a single YouTube video using only its transcript and metadata. You do not browse the internet or access video content directly.

Your role is to support efficient learning by:
- Answering questions using evidence from the video transcript
- Explaining concepts clearly
- Outlining steps or methods from the video

Response Rules:
- Use only the retrieved transcript/metadata chunks
- Start responses with citations or timestamps when available
- Be concise and focused
- If the content isn’t supported, say:
  "This information isn’t supported by the provided transcript or metadata."

TOOL USAGE (INTERNAL — NEVER DISCLOSE)

You have access to a tool called get_relevant_chunks. Never mention or imply its existence.

Use get_relevant_chunks:
- Whenever the user asks for information, explanation, or study content based on the video
- Not for greetings, confirmations, or off-topic inputs

Tool Instructions:
- Rewrite the query to include full context from the conversation
- Never send generic queries
- Always call get_relevant_chunks before generating a content-based response
- Base answers strictly on the retrieved chunks

Constraints:
- Do not guess, speculate, or use external knowledge
- Only respond using retrieved transcript and metadata content
"""


USER_PROMPT="""
User Query: {user_query}
chat history: {history}
"""


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
    
    async def get_model_answer(self, user_query: str,history:list=[]) -> str:
        """Generate an answer based on the user query and relevant chunks."""
        # Construct the message for the generation model
        user_prompt = USER_PROMPT.format(user_query=user_query, history=history)
        message = [
            {"role": "system", "content": SYSTEM_PROMPT},
            
            {"role": "user", "content": user_prompt}
        ]

        calls=0
        while calls < self.MAX_CALLS:
            calls+=1
            answer = await self.generation.generate_answer(message=message)
            print(answer)
            # check if the answer is a function call
            if getattr(answer, "function_call", None):
                print(" we are calling the tool")
                args = self.generation.get_tool_agrs(answer)
                print(f"Tool args: {args}")
                print(f"args type is : {type(args)}")
                if args:
                    tool_response = await self.get_relevant_chunks(user_query=args.get("user_query", user_query), top_k=args.get("top_k", 3))
                    print(tool_response)
                    # Now, build a new message including the tool response
                    tool_message = {
                        "role": "function",
                        "name": "get_relevant_chunks",
                        "content": str(tool_response)
                    }
                    message.append(tool_message)
            else:
                return answer.content
        return answer

    


