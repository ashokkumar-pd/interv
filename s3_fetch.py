import aioboto3
import json
import asyncio
import os
import random

class S3_Fetch():
    def __init__(self):
        # 2️⃣ Create a session (client will be initialized later)
        self.session = aioboto3.Session()
        self.s3_client = None
    
    async def connect(self):
        # 3️⃣ Create an async client once and reuse
        self.s3_client = await self.session.client("s3",aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                                                                                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                                                                                    region_name=os.getenv("AWS_REGION_NAME")).__aenter__()

    async def fetch_json(self, bucket_name, object_key):
        # 4️⃣ Ensure client is connected
        if not self.s3_client:
            raise RuntimeError("S3 client is not connected. Call connect() first.")

        # 5️⃣ Get object from S3
        response = await self.s3_client.get_object(Bucket=bucket_name, Key=object_key)

        # 6️⃣ Read and decode JSON
        file_content = await response["Body"].read()
        file_content = file_content.decode("utf-8")

        # 7️⃣ Parse JSON into Python dict
        json_data = json.loads(file_content)
        if type(json_data)==dict:
            return json_data
        else:
            json_data=json.loads(json_data)
            return json_data
    
    async def close(self):
        # 8️⃣ Close the client when done
        if self.s3_client:
            await self.s3_client.__aexit__(None, None, None)
            self.s3_client = None

    async def question_shortlist(self,question_bank, target_score=100):
        # Flatten the structure into a list of questions with topic & subtopic info
        all_questions = []
        for topic in question_bank["topics"]:
            for subtopic in topic["subtopics"]:
                for q in subtopic["questions"]:
                    all_questions.append({
                        "topic": topic["name"],
                        "subtopic": subtopic["name"],
                        "question": q["question"],
                        "score": q["score"]
                    })

        # Shuffle to randomize selection
        random.shuffle(all_questions)

        selected = []
        total_score = 0

        # Greedy selection to approach target_score
        for q in all_questions:
            if total_score + q["score"] <= target_score or abs((total_score + q["score"]) - target_score) < abs(total_score - target_score):
                selected.append(q)
                total_score += q["score"]

            # If we reached or exceeded target reasonably close, break
            if abs(total_score - target_score) <= 5:  
                break

        return selected, total_score


    async def s3_json_fetcher(self,meeting_id):
        folder_name=os.getenv("AWS_FOLDER_NAME")
        await self.connect()
        data = await self.fetch_json(bucket_name=os.getenv("AWS_S3_BUCKET_NAME"), object_key=f"{folder_name}/{meeting_id}.json")
        questions_list,total_score = await self.question_shortlist(question_bank=data)
        return questions_list,total_score
    
    async def dump_json(self, data,bucket_name, object_key):
        json_str = json.dumps(data)
        json_bytes = json_str.encode("utf-8")
        await self.s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json_bytes,
            ContentType="application/json"
        )
        return f"✅ JSON file uploaded to s3://{bucket_name}/{object_key}"
    
    async def s3_dump_json(self,data,meeting_id,bucket_name, object_key):
        
        folder_name=os.getenv("AWS_ANSWERS_FOLDER_NAME")
        bucket_name=os.getenv("AWS_S3_BUCKET_NAME")
        object_key=f"{folder_name}/{meeting_id}.json"
        if not self.s3_client:
            self.connect()

        # 5️⃣ Get object from S3
        response = await self.dump_json(data=data,bucket_name=bucket_name,object_key=object_key)
