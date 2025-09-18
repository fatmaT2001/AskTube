REDUCE_PROMPT = """
You are given a list of structured summaries from segments of a single AskTube video titled "{video_title}".

Combine these into one short, clear summary (no more than {max_final_words} words) that narrates the flow of the video content.
Describe how the video progresses: what the speaker starts with, what comes next, and how it concludes.
Focus on the sequence of main topics, key facts, and concepts as they appear in the video.
Avoid repetition, speculation, or adding information not present in the original summaries.

Respond with the final summary ONLY, with no introduction or conclusion.
"""