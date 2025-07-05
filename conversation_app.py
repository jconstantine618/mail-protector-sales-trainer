import os
import sys
import json
import random
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational import Conversation

def load_prospects(file_path='data/prospects.json'):
    """Loads prospect profiles from the specified JSON file."""
    print(f"Attempting to load prospects from: {file_path}")
    try:
        with open(file_path, 'r') as f:
            prospects = json.load(f)
            print(f"Successfully loaded {len(prospects)} prospects.")
            return prospects
    except FileNotFoundError:
        print(f"---")
        print(f"Error: The file '{file_path}' was not found.")
        print("Please make sure your Python script is in the 'mail-protector-sales-trainer' root directory.")
        print(f"---")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' contains invalid JSON. Please check its formatting.")
        return None

def main():
    """
    Main function to run the sales training conversation application.
    """
    # --- Configuration ---
    api_key = os.getenv("ELEVENLABS_API_KEY")
    agent_id = "YOUR_AGENT_ID" # IMPORTANT: Replace with your actual agent ID

    # --- Pre-flight Checks ---
    if not api_key:
        print("Error: ELEVENLABS_API_KEY environment variable not set.")
        sys.exit(1)
    if agent_id == "YOUR_AGENT_ID":
        print("Error: Please replace 'YOUR_AGENT_ID' with your actual agent ID in the script.")
        sys.exit(1)

    try:
        client = ElevenLabs(api_key=api_key)
    except Exception as e:
        print(f"Error initializing ElevenLabs client: {e}")
        sys.exit(1)

    # --- Load Prospect Personalities from External JSON File ---
    prospects = load_prospects()
    if not prospects:
        sys.exit(1) # Exit if loading failed.

    # --- Select a Random Prospect for this Training Session ---
    selected_prospect = random.choice(prospects)

    print("\n---")
    print("🚀 This session's prospect is:")
    print(f"   Name: {selected_prospect['prospect_name']}")
    print(f"   Role: {selected_prospect['prospect_role']}")
    print(f"   Company: {selected_prospect['company_name']}")
    print("---\n")

    # --- Callback Functions ---
    def on_user_transcript(transcript: str):
        """Called in real-time as the user (trainee) speaks."""
        print(f"Trainee: {transcript}")

    def on_agent_response(response: str):
        """Called in real-time as the agent (prospect) responds."""
        print(f"Prospect ({selected_prospect['prospect_name']}): {response}")

    def on_conversation_end(conversation_id: str, full_transcript: list):
        """Called when the conversation ends, providing the full transcript for feedback."""
        print(f"\n✅ Conversation {conversation_id} has ended.")
        transcript_filename = f"{conversation_id}_transcript.txt"
        print(f"💾 Saving full transcript to: {transcript_filename}")
        try:
            with open(transcript_filename, "w") as f:
                for message in full_transcript:
                    role = message.get('role', 'unknown').capitalize()
                    text = message.get('text', '')
                    f.write(f"{role}: {text}\n")
            print("Transcript saved successfully.")
        except IOError as e:
            print(f"Error saving transcript: {e}")

    # --- Main Execution ---
    print("Starting conversation... Speak into your microphone to begin.")
    print("Press Ctrl+C to end the conversation at any time.")

    conversation = Conversation(
        client=client,
        agent_id=agent_id,
        callback_user_transcript=on_user_transcript,
        callback_agent_response=on_agent_response,
        callback_on_end=on_conversation_end,
    )

    try:
        # Start the conversation and inject the selected prospect's personality
        conversation.start(variables=selected_prospect)
    except KeyboardInterrupt:
        print("\n🛑 Conversation interrupted by user. Shutting down...")
        conversation.stop()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        if 'conversation' in locals():
            conversation.stop()

if __name__ == "__main__":
    main()
