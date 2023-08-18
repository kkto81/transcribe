class TranscriptParser:
    def __init__(self, transcript_json):
        self.transcript_json = transcript_json

    def parse_transcript(self):
        items = self.transcript_json["results"]["items"]

        speaking_segments = []
        last_speaker = None
        for item in items:
            if "speaker_label" in item and (
                item["type"] == "pronunciation" or item["type"] == "punctuation"
            ):
                current_speaker = item["speaker_label"]

                # If the current speaker is different from the last speaker, start a new speaking segment
                if current_speaker != last_speaker:
                    speaking_segments.append(
                        {"speaker": current_speaker, "content": []}
                    )
                    last_speaker = current_speaker

                # Append the current word/punctuation to the current speaking segment
                speaking_segments[-1]["content"].append(
                    item["alternatives"][0]["content"]
                )

        # Combine each speaker's segments into complete sentences and store in output
        output = "\n".join(
            [
                f'{segment["speaker"]}: {"".join(segment["content"])}'
                for segment in speaking_segments
            ]
        )

        return output

    def get_corrected_transcript(self, openai_service):
        # Convert the transcript to a single string
        transcript = self.parse_transcript()

        # Correct the transcript using OpenAI
        corrected_transcript = openai_service.correct_text(transcript)

        return corrected_transcript
