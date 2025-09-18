MAP_PROMPT = """
You will be given a chunk from a longer YouTube video.

Summarize this chunk by briefly describing its main content and purpose.

### Language
- Write the summary in the SAME language as the input chunk.

### SUMMARY
- Be concise and clear (≤ 360 words).
- Focus on what this chunk is about and what the viewer learns or sees.
- Mention any important topics, facts, or concepts covered.
- Avoid filler, speculation, or repetition.
- If the chunk has almost no substantive content, return an empty string "".

- **Return SUMMARY ONLY**. No prose, no explanations, and no intro or conclusion.
If you are unsure, keep the output minimal but valid.
"""