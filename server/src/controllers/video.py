from urllib.parse import urlparse, parse_qs
import requests
from ..utils.settings import get_settings
from typing import List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


class VideoController:
    def __init__(self):
        self.youtube_api= YouTubeTranscriptApi()
        pass

    def _extract_youtube_id(self,url: str) -> str | None:
        """Extract the video ID from a YouTube URL."""
        parsed = urlparse(url)

        # Standard: https://www.youtube.com/watch?v=ID
        if parsed.hostname in ["www.youtube.com", "youtube.com"]:
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]

        # Short: https://youtu.be/ID
        if parsed.hostname == "youtu.be":
            return parsed.path.lstrip("/")

        # Embed: https://www.youtube.com/embed/ID
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]

        return None
    


    
    def _fetch_youtube_title(self,video_id: str) -> str | None:
        """Fetch the video title from YouTube Data API v3."""
        url = (
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=snippet&id={video_id}&key={get_settings().YOUTUBE_API_KEY}"
        )
        resp = requests.get(url)
        data = resp.json()

        items = data.get("items", [])
        if items:
            return items[0]["snippet"]["title"]
        return None


    def _get_transcript_langs(self,transcript_list: list) -> List[dict]:
        """
        Returns list of available transcript language codes 
        """
        try:
            transcript_langs = [
                {
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "auto_generated": transcript.is_generated,
                    "transcript": transcript
               
                }    

                for transcript in transcript_list
            ]

            return transcript_langs

        except Exception as e:
            print(f"Error fetching transcripts: {e}")
            return []
        

    def _check_transcript_available(self,transcript_langs: list, target_language: str = "en") -> bool:
        """
        Check if a transcript is available for the given language code prefix ('en' or 'ar').
        """
        try:
            target_transcript=None
            for transcript in transcript_langs:
                language_code = transcript.get("language_code", "")
                if language_code.startswith(target_language):
                    target_transcript=transcript.get("transcript")
                    return True,target_transcript
            return False,target_transcript
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            print(f"Transcript error: {e}")
            return False,target_transcript
    

    def _get_transcript(self,video_id: str, target_language: str = "en"):
        """
        Fetch transcript for the first matching language code 
        that starts with the given prefix ('en' or 'ar').
        Returns a list of dicts [{'text','start','duration'}] or None.
        """
        try:
            is_available,transcript=None,None
            transcript_list = self.youtube_api.list(video_id)
            # Get available transcripts
            listing = self._get_transcript_langs(transcript_list=transcript_list)
            # check if target language is available
            is_available,transcript = self._check_transcript_available(transcript_langs=listing, target_language=target_language)
            if not is_available:
                return is_available, transcript
            
            # get the transcript object for the target language code
            transcript =transcript.fetch()

            return is_available, transcript
                
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            print(f"Transcript error: {e}")
            return None
        
    
    def get_video_info(self, youtube_link: str):
        # Logic to extract video info from YouTube link
        video_id = self._extract_youtube_id(youtube_link)
        if not video_id:
            return None
        
        video_title = self._fetch_youtube_title(video_id)
        if not video_title:
            return None
        
        is_available, transcript = self._get_transcript(video_id, target_language="en")

        
        return {
            "video_id": video_id,
            "title": video_title,
            "transcript_available": is_available,
            "transcript": transcript
        }