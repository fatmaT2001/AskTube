

#  preprocess the video transcript text for NLP tasks
#  chunk the text into smaller segments
#  prepare the chunks and the metadata for embedding generation

from typing import List, Dict, Any
from youtube_transcript_api import FetchedTranscript

class NLPController:
    def __init__(self):
        pass

    def _preprocess_youtube_transcript(self, transcript: FetchedTranscript) -> List[Dict[str, Any]]:
        """
        Preprocess the YouTube transcript for NLP tasks.
        Splits the transcript into smaller chunks with metadata.
        
        Args:
            transcript (FetchedTranscript): The transcript object fetched from YouTube.
            it is a list of FetchedTranscriptSnippet objects with attributes 'text', 'start', and 'duration'.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing text chunks and their metadata.
        """
        try:
            processed_transcript = []
            for snippet in transcript.snippets:
                chunk = {
                    "text": snippet.text,
                    "start": snippet.start,
                    "duration": snippet.duration,
                    "end": snippet.start + snippet.duration
                }
                processed_transcript.append(chunk)
            return processed_transcript
        except Exception as e:
            print(f"Error preprocessing transcript: {e}")
            return []
        

    def _chunk_text(self, processed_transcript: List[Dict[str, Any]], chunk_duration: int) -> List[str]:
        """
        Chunk the processed transcript into smaller segments based on chunk_duration.

        Args:
            processed_transcript (List[Dict[str, Any]]): The preprocessed transcript with metadata.
            chunk_duration (int): The duration of each chunk in seconds.

        Returns:
            List[str]: A list of text chunks.
        """
        chunks = []
        current_chunk = []
        current_duration = 0.0

        for snippet in processed_transcript:
            # If adding this snippet exceeds the chunk_duration, start a new chunk
            if current_duration + snippet["duration"] > chunk_duration and current_chunk:
                # Join texts in the current chunk and add to chunks
                current_chunk_text = " ".join([s["text"] for s in current_chunk])
                chunks.append({
                    "text": current_chunk_text,
                    "start": current_chunk[0]["start"],
                    "end": current_chunk[-1]["end"],
                })
                current_chunk = []
                current_duration = 0.0

            current_chunk.append(snippet)
            current_duration += snippet["duration"]

        # Add the last chunk if any
        if current_chunk:
            current_chunk_text = " ".join([s["text"] for s in current_chunk])
            chunks.append({
                "text": current_chunk_text,
                "start": current_chunk[0]["start"],
                "end": current_chunk[-1]["end"],
            })

        return chunks
    

    def prepare_youtube_transcript_for_embedding(self, transcript: FetchedTranscript,chunk_duration:int) -> List[Dict[str, Any]]:
        """
        Prepare the text chunks and their metadata for embedding generation.

        Args:
            chunks (List[Dict[str, Any]]): The list of text chunks with metadata.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries ready for embedding generation.
        """

        # Preprocess the transcript
        processed_transcript = self._preprocess_youtube_transcript(transcript=transcript)
        print(f"len of processed transcript: {len(processed_transcript)}")
        # Chunk the text into smaller segments
        chunks = self._chunk_text(processed_transcript=processed_transcript, chunk_duration=chunk_duration)
        print(f"len of chunks: {len(chunks)}")
        embedding_ready_data=[

            {
                "text": chunk["text"],
                "duration": {
                    "start": chunk["start"],
                    "end": chunk["end"]
                }
            }

            for chunk in chunks
        ]
        print(f"len of embedding ready data: {len(embedding_ready_data)}")
        return embedding_ready_data
        

