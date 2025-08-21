from langchain_openai import AzureChatOpenAI
import os
import re

from prompts import scoring_prompt

class Scoring():


    def __init__(self, meeting_id: str):
        super().__init__()
        try:
            print(f"Initializing Scoring for meeting_id: {meeting_id}")
            self.meeting_id = meeting_id
            self.llm = AzureChatOpenAI(
                api_key=os.getenv("AZURE_API_KEY"),
                azure_endpoint=os.getenv("AZURE_ENDPOINT"),
                azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
                openai_api_version=os.getenv("OPENAI_API_VERSION"),
            )
        except Exception as e:
            print(f"Failed to initialize AsyncQuestionGenerator: {str(e)}")
            raise
    async def llm_call(self, jd: str = "") -> str:
        self.logger.info("Starting LLM call for question generation")
        try:
            prompt = scoring_prompt.replace("{answers}", jd)
            self.logger.debug("Prepared prompt for LLM invocation")
            output = await self.llm.ainvoke(prompt)
            raw_output = output.content
            cleaned_output = re.sub(
                r"^```json\s*([\s\S]*?)\s*```$",
                r"\1",
                raw_output.strip(),
                flags=re.MULTILINE
            )
            print("Successfully generated and cleaned LLM output")
            return cleaned_output
        except Exception as e:
            self.logger.error(f"Error in LLM call: {str(e)}")
            raise