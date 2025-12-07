import streamlit as st
import os
import time
import wave
import pyaudio
from pydub import AudioSegment
from audiorecorder import audiorecorder
import hashlib
from constants import Constants as ct

def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成
    """
    audio = audiorecorder(
        start_prompt=ct.RECORD_START_PROMPT,
        pause_prompt=ct.RECORD_PAUSE_PROMPT,
        stop_prompt=ct.RECORD_STOP_PROMPT,
        start_style=ct.RECORD_START_STYLE,
        pause_style=ct.RECORD_PAUSE_STYLE,
        stop_style=ct.RECORD_STOP_STYLE
    )
    if len(audio) > 0:
        # 直前と同じ録音を再処理しないためのハッシュチェック（Streamlit再実行対策）
        try:
            buf = audio.raw_data
        except Exception:
            # raw_data が取得できない場合は一旦エクスポートしてファイルの内容でハッシュ
            tmp_path = f"{audio_input_file_path}.tmp"
            audio.export(tmp_path, format="wav")
            with open(tmp_path, "rb") as f:
                buf = f.read()
            os.remove(tmp_path)
        md5 = hashlib.md5(buf).hexdigest()
        last_md5 = st.session_state.get("last_audio_md5")
        if last_md5 == md5:
            # 同一音声は無視（例えば速度変更などのUI操作による再実行時）
            st.stop()
        # 新規音声として処理
        st.session_state.last_audio_md5 = md5
        audio.export(audio_input_file_path, format="wav")
    else:
        st.stop()

def transcribe_audio(audio_input_file_path):
    """
    音声入力ファイルから文字起こしテキストを取得
    引数:
        audio_input_file_path: 音声入力ファイルのパス
    """
    with open(audio_input_file_path, 'rb') as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model=ct.TRANSCRIPTION_MODEL,
            file=audio_input_file,
            language=ct.TRANSCRIPTION_LANGUAGE
        )
    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)
    return transcript

def save_to_wav(llm_response_audio, audio_output_file_path):
    """
    一旦mp3形式で音声ファイル作成後、wav形式に変換
    引数:
        llm_response_audio: LLMからの回答の音声データ
        audio_output_file_path: 出力先のファイルパス
    """
    temp_audio_output_filename = f"{ct.AUDIO_OUTPUT_DIR}/{ct.TEMP_MP3_PREFIX}{int(time.time())}.mp3"
    with open(temp_audio_output_filename, "wb") as temp_audio_output_file:
        temp_audio_output_file.write(llm_response_audio)
    audio_mp3 = AudioSegment.from_file(temp_audio_output_filename, format="mp3")
    audio_mp3.export(audio_output_file_path, format="wav")
    # 音声出力用に一時的に作ったmp3ファイルを削除
    os.remove(temp_audio_output_filename)

def play_wav(audio_output_file_path):
    """
    音声ファイルの読み上げ
    引数:
        audio_output_file_path: 音声ファイルのパス
    """
    # 音声ファイルの読み込み
    _ = AudioSegment.from_wav(audio_output_file_path)
    # PyAudioで再生
    with wave.open(audio_output_file_path, 'rb') as play_target_file:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(play_target_file.getsampwidth()),
            channels=play_target_file.getnchannels(),
            rate=play_target_file.getframerate(),
            output=True
        )
        data = play_target_file.readframes(ct.AUDIO_CHUNK_SIZE)
        while data:
            stream.write(data)
            data = play_target_file.readframes(ct.AUDIO_CHUNK_SIZE)
        stream.stop_stream()
        stream.close()
        p.terminate()
    # LLMからの回答の音声ファイルを削除
    os.remove(audio_output_file_path)

def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生
    """
    # 問題文を生成するChainを実行し、問題文を取得
    problem = st.session_state.chain_create_problem.predict(input="")
    # LLMからの回答を音声データに変換
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model=ct.AUDIO_MODEL,
        voice=ct.AUDIO_VOICE,
        input=problem,
        speed=st.session_state.speed
    )
    # 音声ファイルの作成
    audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/{ct.AUDIO_OUTPUT_FILENAME_PREFIX}{int(time.time())}.wav"
    save_to_wav(llm_response_audio.content, audio_output_file_path)
    # 音声ファイルの読み上げ
    play_wav(audio_output_file_path)
    return problem, llm_response_audio
