import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "The Cutest Baby Fish Spa Moments",
        "Baby's First Fish Spa Experience",
        "Tiny Toes, Happy Fishes — Baby Spa Fun",
        "Watch This Baby Enjoy a Fish Spa",
        "Adorable Baby Having the Best Spa Day",
        "The Joy of a Baby Fish Spa",
        "Baby Smiles and Tickling Fishes",
        "This Baby Loves Her Fish Spa",
        "Little Feet, Little Fish, Big Smiles",
        "Baby Spa Time — Pure Cuteness",
        "The Sweetest Fish Spa Ever",
        "Baby's Relaxing Fish Spa Session",
        "Ticklish Little Baby at the Fish Spa",
        "Giggles and Fishes: Baby Spa Joy",
        "A Baby's Perfect Fish Spa Day",
    ]

    fallback_descriptions = [
        "Look at this little one having the time of her life at the fish spa! The tiny fish gently tickle her feet while she giggles with pure joy. It's the cutest thing you'll see today. Babies and fish — what a perfect combo. Drop a 😍 if this made you smile! #babyspa #fishspa #babyfun #cutebaby #babyrelaxation #fishspababy #adorable #babygiggle #parenthood #happybaby",
        "Have you ever seen a baby this relaxed? Surrounded by gentle little fish, this cutie is living her best spa day. The fish softly nibble her feet while she splashes and smiles. Pure happiness in a tiny package. Double tap if you can't handle the cuteness! 💕 #babyspa #fishspa #cutebaby #babyrelaxation #spaday #tinytoes #fishspababy #happybaby #parenthood #cutenessoverload",
        "Fish spa day for this adorable baby! The little fish swim up to say hello and give her the gentlest tickle. She's not scared at all — just giggles and splashes. Babies are braver than we think! Save this to brighten your day. 🐟 #fishspa #babyspa #babyfun #cutebaby #spaexperience #fishybites #happybaby #giggle #parenthood #adorable",
        "There's nothing sweeter than a baby enjoying her fish spa. The tiny fish dance around her feet while she watches them with pure wonder. It's calming, cute, and completely adorable. Watch the joy on her face! Drop a ❤️ for this little cutie! #babyspa #fishspa #cutebaby #wonder #babyjoy #fishyfriends #spaday #parenthood #adorable #blessed",
        "This baby is a natural at the fish spa! She sits calmly while the little fish give her the spa treatment. Some babies would cry — this one is pure zen. What a champ! Like if you love watching happy babies! 💛 #babyspa #fishspa #zenbaby #cutebaby #relaxing #fishspababy #spaday #babyzen #parenthood #cute",
        "First fish spa, and this baby is already a pro. The gentle fish tickle her toes and she can't stop laughing. It's the most precious spa session ever recorded. Watch till the end for the biggest smile! 🐟✨ #fishspa #babyspa #firsttime #cutebaby #laughingbaby #fishyfun #happybaby #parenthood #adorable #spaday",
        "Some babies play with toys — this one plays with fish! Her fish spa session is full of giggles, splashes, and pure joy. The fish seem to love her just as much. It's a love story between a baby and her fishy friends. 💕 #babyspa #fishspa #fishyfriends #cutebaby #babyfun #giggle #happybaby #parenthood #adorable #friendship",
        "Watch this tiny tot melt into the ultimate relaxation at the fish spa. The gentle fish work their magic while she enjoys every second. Even babies need a spa day, right? Save this for your daily dose of cuteness! 🌸 #babyspa #fishspa #relaxation #cutebaby #spaday #zenbaby #fishspababy #parenthood #happybaby #cute",
        "This adorable baby discovered the joy of a fish spa, and there's no going back. The little fish tickle her feet and she's all smiles. Her laugh is contagious! Double tap if this made your day! 😊 #babyspa #fishspa #babyjoy #cutebaby #laughingbaby #fishyfun #happybaby #parenthood #adorable #bliss",
        "Tiny feet, tiny fish, and a whole lot of happiness. This baby's fish spa session is the definition of adorable. The fish gently nibble while she splashes with delight. Pure baby bliss! Drop a 🐟 if you love this! #babyspa #fishspa #tinytoes #cutebaby #babybliss #fishyfriends #happybaby #parenthood #adorable #joy",
        "This baby is officially a fish spa regular! Look how calm and happy she is as the fish swim around her. It's like her own little private spa. Who knew babies could be so bougie? 😂 Like if this made you laugh! #babyspa #fishspa #spoiledbaby #cutebaby #babyfun #fishyfun #happybaby #parenthood #cute #spaday",
        "The most relaxing baby in the world right here! Fish spa, gentle water, and zero worries. This little one has mastered the art of relaxation. We could all learn from her. Save this for a moment of peace! 🧘‍♀️ #babyspa #fishspa #relaxation #zenbaby #cutebaby #spaday #fishspababy #parenthood #happybaby #peace",
        "Babies + fish spa = the cutest combination ever. This little cutie giggles as the fish tickle her tiny toes. Her happiness is contagious! Watch this and try not to smile — we dare you. 😍 #babyspa #fishspa #cutecombination #cutebaby #giggle #fishyfun #happybaby #parenthood #adorable #smile",
        "This baby just had the best day ever at the fish spa. The little fish gave her the royal treatment while she soaked up all the love. Her smile says it all. Share this with a mom friend who needs a smile today! 💕 #babyspa #fishspa #bestday #cutebaby #happybaby #fishyfriends #parenthood #spaday #cute #blessed",
        "Nothing beats a baby's fish spa day — soft water, gentle fish, and endless giggles. This little one is living her best life and we're just here for it. Comment if you'd take your baby to a fish spa! 🐟 #babyspa #fishspa #babyfun #cutebaby #giggle #fishyfriends #parenthood #spaday #happybaby #cute",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "adorable and warm — speak as a delighted parent watching their baby",
        "playful and joyful — make viewers smile at the baby's happiness",
        "gentle and soothing — match the calm, relaxing spa mood",
        "excited and bubbly — celebrate the cuteness of the moment",
        "sweet and heartwarming — make viewers feel warm and happy",
        "fun and lighthearted — bring a laugh and a smile",
        "tender and loving — emphasise how precious the baby is",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'BabySteps FishSpa'. "
        f"It features adorable babies enjoying a fish spa - relaxing in a small pool where tiny fish "
        f"gently swim around and tickle their feet. It's cute, wholesome, heartwarming baby content "
        f"that brings smiles to parents and viewers. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this made you smile! Comment if you'd take your baby to a fish spa! Share this with a mom friend! Follow BabySteps FishSpa for more adorable baby moments! "
        f"Include relevant hashtags in ALL LOWERCASE such as #babyspa #fishspa #cutebaby #babyfun #babyrelaxation #fishspababy #adorable #parenthood #babygiggle #happybaby #spaday #toddler #cute #babysteps. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["babyspa", "fishspa", "cutebaby", "babyfun", "babyrelaxation", "fishspababy", "adorable", "parenthood", "babygiggle", "happybaby", "spaday", "toddler", "cute", "babysteps"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
