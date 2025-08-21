import azure.cognitiveservices.speech as speechsdk
import os
import asyncio

class STT():
    def __init__(self,websocket,loop) -> None:
        self.websocket =websocket
        self.loop=loop
        self.transcriptions=[]
        self.speech_config = speechsdk.SpeechConfig(subscription=os.getenv('SPEECH_KEY'), endpoint=os.getenv('STT_ENDPOINT'))
        # self.speech_config.speech_recognition_language = os.getenv("SPEECH_LANGUAGE")

        # Use AudioStreamReader to handle raw audio chunks
        self.audio_stream = speechsdk.audio.PushAudioInputStream()
        self.audio_config = speechsdk.audio.AudioConfig(stream=self.audio_stream)
        self.recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=self.audio_config)

        self.recognizer.recognized.connect(self.recognized)
        self.recognizer.session_stopped.connect(self.session_stopped)
        self.recognizer.start_continuous_recognition()

    async def write_and_get_text(self, audio_chunk: bytes):
        # Create a new future and write the chunk
        self.pending_future = self.loop.create_future()
        self.audio_stream.write(audio_chunk)

        # Wait until recognized() resolves it
        result = await self.pending_future
        return result
    
    def recognized(self,evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text
            self.transcriptions.append(text)
            print(f"message returned: {text}")
            future = asyncio.run_coroutine_threadsafe(self.websocket.send_json({"text": text}), self.loop )
            
                
    def session_stopped(self,evt):
        self.audio_stream.close()
