# AWSService.py
import boto3
import os
import time
from botocore.exceptions import NoCredentialsError


class AWSService:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name

        # Set up boto3 S3 and Transcribe clients with API keys from environment variables
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("TRANSCRIBE_POC_AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("TRANSCRIBE_POC_AWS_SECRET_ACCESS_KEY"),
        )
        self.transcribe = boto3.client(
            "transcribe",
            aws_access_key_id=os.getenv("TRANSCRIBE_POC_AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("TRANSCRIBE_POC_AWS_SECRET_ACCESS_KEY"),
        )
        # プロファイル名で指定する場合
        # session = boto3.Session(profile_name='kkto81')
        # self.s3 = session.client('s3')
        # self.transcribe = session.client('transcribe')

    def upload_to_s3(self, file_name):
        try:
            # Upload file to S3
            with open(file_name, "rb") as data:
                self.s3.upload_fileobj(
                    data, self.bucket_name, os.path.basename(file_name)
                )
            return True
        except NoCredentialsError:
            return False

    def delete_from_s3(self, file_name):
        try:
            # Delete file from S3
            self.s3.delete_object(
                Bucket=self.bucket_name, Key=os.path.basename(file_name)
            )
            print("File deleted successfully from S3")
            return True
        except Exception as e:
            print("Error deleting file from S3:", e)
            return False

    def start_transcription_job(self, file_name, language_code, speaker_count):
        job_name = "my_transcribe_job_" + str(int(time.time()))
        job_uri = f"s3://{self.bucket_name}/{os.path.basename(file_name)}"

        # ファイルの拡張子を取得（例：.wav, .mp3）
        file_extension = os.path.splitext(file_name)[1].lower()

        # 拡張子に応じてMediaFormatを設定
        if file_extension == ".mp3":
            media_format = "mp3"
        elif file_extension in [".mp4", ".m4a"]:
            media_format = "mp4"
        elif file_extension == ".wav":
            media_format = "wav"
        elif file_extension == ".flac":
            media_format = "flac"
        elif file_extension == ".ogg":
            media_format = "ogg"
        elif file_extension in [".amr", ".awb"]:
            media_format = "amr"
        elif file_extension == ".webm":
            media_format = "webm"
        else:
            # 未知の拡張子の場合はエラーメッセージを表示
            print("Unsupported file extension, please use a supported media format")
            return None

        self.transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": job_uri},
            MediaFormat=media_format,
            LanguageCode=language_code,
            Settings={"ShowSpeakerLabels": True, "MaxSpeakerLabels": speaker_count},
        )

        return job_name

    def get_transcription_job(self, job_name):
        return self.transcribe.get_transcription_job(TranscriptionJobName=job_name)

    def delete_transcription_job(self, job_name):
        try:
            self.transcribe.delete_transcription_job(TranscriptionJobName=job_name)
            print("Deleted Transcription Job:", job_name)
        except Exception as e:
            print("Error Deleting Transcription Job:", e)
