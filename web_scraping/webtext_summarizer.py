import bs4
import requests
from transformers import pipeline


def fetch_and_parse(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        return text
    except requests.exceptions.RequestException as e:
        print(f'Error fetching URL {url}: {e}')
        return ''


class TextSummarizer:
    summarizer = pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')

    def summarize(self, text, max_chunk_length=800):
        try:
            summary = ''

            # Split the text into chunks that fit within the model's limit
            text_chunks = [text[i : i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]

            # Summarize each chunk and append to the overall summary
            for chunk in text_chunks:
                chunk_summary = self.summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
                summary += chunk_summary + ' '

            return summary.strip()
        except Exception as e:
            print(f'Error during summarization: {e}')
            return ''


if __name__ == '__main__':
    text = fetch_and_parse('https://en.wikipedia.org/wiki/What_Is_Life%3F')
    print(text)
    summarizer = TextSummarizer()
    print('\n\n====================\n\n')
    print(summarizer.summarize(text))
