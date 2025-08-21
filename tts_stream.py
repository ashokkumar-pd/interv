import os
import azure.cognitiveservices.speech as speechsdk
# import pyaudio
class StreamTTS():
    def __init__(self) -> None:
        print("KEY:", os.getenv('SPEECH_KEY'))
        print("ENDPOINT:", os.getenv('ENDPOINT'))

        self.speech_config = speechsdk.SpeechConfig(subscription=os.getenv('SPEECH_KEY'), endpoint=os.getenv('TTS_ENDPOINT'))
        self.speech_config.speech_synthesis_voice_name='en-US-AvaMultilingualNeural'
        self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm)
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config = self.speech_config,audio_config=None)
    def synthesize_speech_to_bytes(self,text):
        result = self.speech_synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Synthesis complete")
            return result.audio_data  # This is raw PCM or compressed format depending on config
        else:
            print(f"❌ Synthesis failed: {result.reason}")
            return None

# def play_audio_bytes_old(audio_bytes):
#     p = pyaudio.PyAudio()
#     stream = p.open(format=pyaudio.paInt16,  # Azure default is 16-bit PCM
#                     channels=1,
#                     rate=16000,
#                     output=True)

#     stream.write(audio_bytes)
#     stream.stop_stream()
#     stream.close()
#     p.terminate()

import sounddevice as sd
import numpy as np

def play_audio_bytes(audio_bytes):
    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
    sd.play(audio_array, samplerate=16000)
    sd.wait()

if __name__ == "__main__":
    audio_bytes = synthesize_speech_to_bytes("Hello, this is Azure speech streamed into Python and played manually.")
    if audio_bytes:
        play_audio_bytes(audio_bytes)
