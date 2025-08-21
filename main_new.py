from fastapi import FastAPI,WebSocket
import os
import numpy as np
import asyncio
import time
import json
from dotenv import load_dotenv

from stt import STT
from tts_stream import StreamTTS
from s3_fetch import S3_Fetch
from scoring import Scoring


app=FastAPI()
load_dotenv()

class Questions():
    def __init__(self):
        self.questions_list=[]
        self.answers=[]
        self.question_data=False

@app.websocket("/ws/speech")
async def websocket_endpoint(websocket:WebSocket):
    
    await websocket.accept()
    loop=asyncio.get_event_loop()
    stt_obj = STT(websocket=websocket,loop=loop)
    tts_stream_obj=StreamTTS()
    questions_obj=Questions()
    try:
        while True:

            message = await websocket.receive()
            # import pdb;pdb.set_trace()
            if message["type"]=="websocket.receive":
                if isinstance(message.get("bytes"),bytes):
                    data=message["bytes"]
                    if len(data)%2 !=0:
                        data = data[:len(data)-(len(data)%2)]
                    data = np.frombuffer(data,dtype=np.int16)
                    audio_data_bytes=data.tobytes()
                    # text = await stt_obj.write_and_get_text(audio_chunk=audio_data_bytes)
                    # print(text)
                    stt_obj.audio_stream.write(audio_data_bytes)
                    
                elif isinstance(message.get("text"),str):
                    meeting_data = json.loads(message["text"])
                    if meeting_data["type"] == "end":
                        if questions_obj.question_data:
                            questions_obj.question_data["answer"]=' '.join(stt_obj.transcriptions)
                            questions_obj.answers.append(questions_obj.question_data)
                            stt_obj.transcriptions=[]
                        else:
                            stt_obj.transcriptions=[]
                        print("Received end signal, stopping recognition")
                    # elif meeting_data["type"]=="ask_question":
                        questions_obj.question_data = questions_obj.questions_list.pop()
                        question =questions_obj.question_data["question"]
                        audio_stream = tts_stream_obj.synthesize_speech_to_bytes(text=question)
                        await websocket.send_bytes(audio_stream)
                        await websocket.send_json({"type":"transcription", "text":question})
                    elif meeting_data["type"]=="meeting_id":
                        meeting_id=meeting_data["value"]
                        s3_obj = S3_Fetch()
                        questions_obj.questions_list,total_score = await s3_obj.s3_json_fetcher(meeting_id=meeting_id)
                        print("here is the :",len(questions_obj.questions_list))
                        print("S3 Bucket fetching requested")
                    elif meeting_data["type"]=="intro":
                        intro_text="Hello, welcome to the interview! I'm your virtual interviewer today. Let’s have a great conversation—ready to get started?"
                        audio_stream = tts_stream_obj.synthesize_speech_to_bytes(text=intro_text)
                        await websocket.send_bytes(audio_stream)
                        await websocket.send_json({"type":"transcription", "text":intro_text})
                    elif meeting_data["type"]=="endCall":
                        questions_obj.question_data["answer"]=' '.join(stt_obj.transcriptions)
                        questions_obj.answers.append(questions_obj.question_data)
                        output_json_data = json.dumps(questions_obj.answers)
                        print(questions_obj.answers)
                else:
                    print(f"Unexpected message type: {message}")

    except Exception as e:
        print(f"Websocket Error : {e}")
    finally:
        stt_obj.recognizer.stop_continuous_recognition()
        stt_obj.audio_stream.close()
        await websocket.close()
        print("WebSocket connection closed")
