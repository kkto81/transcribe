import openai
import os


class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def correct_text(self, text):
        # Break the text into chunks of around 2000 characters
        chunks = []
        chunk = ""
        for line in text:
            if len(chunk) + len(line) < 1000:
                chunk += line
            else:
                chunks.append(chunk)
                chunk = line
        chunks.append(chunk)  # Don't forget the last chunk

        # Iterate over the chunks and use OpenAI to correct each chunk
        corrected_chunks = []
        for chunk in chunks:
            # Define system message
            system = {
                "role": "system",
                "content": "以下は、spk_0 と spk_1 ... の会話なのですが、AIによる文字起こしでテキストを生成したため、所々おかしな文章が混じっています。これを会話の流れが自然になるように、補正してもらえないでしょうか。元の文の表現や言葉を可能な限り保持しつつ、意味が通るように修正お願いいたします。",
            }
            # Define user message
            user = {"role": "user", "content": chunk}

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                # model="gpt-4",
                messages=[system, user],
                max_tokens=2000,
            )

            corrected_chunks.append(
                response["choices"][0]["message"]["content"].strip()
            )

        # Join the corrected chunks back into a single transcript
        corrected_transcript = " ".join(corrected_chunks)

        return corrected_transcript
