from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QTextEdit,
    QComboBox,
    QLabel,
)
from botocore.exceptions import NoCredentialsError
import os
import sys
import time
import requests
import pyperclip

from services.AWSService import AWSService
from services.OpenAIService import OpenAIService
from utils.TranscriptParser import TranscriptParser


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Speech to Text POC App")
        self.resize(800, 600)

        # Widget and layout
        self.layout = QVBoxLayout()
        self.widget = QWidget()

        # Language selection combo box
        self.language_label = QLabel("言語選択:")
        self.layout.addWidget(self.language_label)
        self.language_box = QComboBox()
        self.language_box.addItem("日本語", "ja-JP")
        self.language_box.addItem("英語", "en-US")
        self.layout.addWidget(self.language_box)

        # Speaker selection combo box
        self.speaker_label = QLabel("話者数:")
        self.layout.addWidget(self.speaker_label)
        self.speaker_box = QComboBox()
        for i in range(1, 7):  # Add numbers 1 through 6
            self.speaker_box.addItem(str(i), i)
        self.speaker_box.setCurrentIndex(1)  # Default to 2 speakers
        # self.speaker_box.setCurrentIndex(2)  # Default to 3 speakers
        self.layout.addWidget(self.speaker_box)

        # Upload & Transcribe button
        self.transcribe_label = QLabel("アップロード＆音声解析:")
        self.layout.addWidget(self.transcribe_label)
        self.transcribe_button = QPushButton("Upload and Transcribe")
        self.transcribe_button.clicked.connect(self.upload_and_transcribe)
        self.layout.addWidget(self.transcribe_button)

        # Text edit field
        self.text_edit = QTextEdit()
        self.layout.addWidget(self.text_edit)

        # Set layout
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.file_name = None
        self.bucket_name = "newspicks-cx-transcribe"
        self.aws_service = AWSService(self.bucket_name)
        self.openai_service = OpenAIService()

    def upload_and_transcribe(self):
        def show_message(message):
            self.text_edit.append(message)
            QApplication.processEvents()

        def clear_message():
            self.text_edit.clear()
            QApplication.processEvents()

        # Upload file
        self.file_name, _ = QFileDialog.getOpenFileName(
            self, "Upload File", os.getenv("HOME")
        )
        if self.file_name:
            # Check if the selected file is a common audio file format
            if not self.file_name.lower().endswith(
                (".wav", ".mp3", ".mp4", ".m4a", ".flac")
            ):
                self.text_edit.append(
                    "The selected file is not a common audio file format."
                )
                return

            # Upload file to S3
            show_message("Start Upload File")
            if self.file_name and self.aws_service.upload_to_s3(self.file_name):
                show_message(
                    f"Successfully uploaded {os.path.basename(self.file_name)} to {self.bucket_name}"
                )

            # Transcribe file
            show_message("Start Transcribe File")
            job_name = self.aws_service.start_transcription_job(
                self.file_name,
                self.language_box.currentData(),
                self.speaker_box.currentData(),
            )
            while True:
                status = self.aws_service.get_transcription_job(job_name)
                if status["TranscriptionJob"]["TranscriptionJobStatus"] in [
                    "COMPLETED",
                    "FAILED",
                ]:
                    break
                show_message("Now Processing...")
                time.sleep(5)

            if status["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
                response_url = status["TranscriptionJob"]["Transcript"][
                    "TranscriptFileUri"
                ]
                response = requests.get(response_url)
                data = response.json()
                parser = TranscriptParser(data)
                # output = parser.parse_transcript()
                corrected_output = parser.get_corrected_transcript(self.openai_service)
                clear_message()
                show_message(corrected_output)
                pyperclip.copy(corrected_output)
                self.aws_service.delete_transcription_job(job_name)
                self.aws_service.delete_from_s3(self.file_name)
            else:
                show_message("Transcription Failed")
                self.aws_service.delete_transcription_job(job_name)
                self.aws_service.delete_from_s3(self.file_name)


def main():
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
