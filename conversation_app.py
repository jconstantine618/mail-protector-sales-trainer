import os
import sys
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational import Conversation

def main():
    """
    This script runs a real-time, voice-to-voice conversation with an ElevenLabs agent.
    It prints the user and agent transcripts as they happen and saves the full
    conversation to a text file upon completion.
    """
    
    # --- Configuration ---
    # It's highly recommended to set your API key as an environment variable
    # for security. You can also hardcode it here for quick testing.
    # Example: api_key = "YOUR_ELEVENLABS_API_KEY"
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    # Replace this with the ID of the agent you created in your ElevenLabs dashboard.
    agent_id = "YOUR_AGENT_ID"
    
    # --- Pre-flight Checks ---
    if not api_key:
        print("Error: ELEVENLABS_API_KEY environment variable not set.")
        print("Please set the variable or hardcode your API key in the script.")
        sys.exit(1)
        
    if agent_id == "YOUR_AGENT_ID":
        print("Error: Please replace 'YOUR_AGENT_ID' with your actual agent ID.")
        sys.exit(1)

    try:
        client = ElevenLabs(api_key=api_key)
    except Exception as e:
        print(f"Error initializing ElevenLabs client: {e}")
        sys.exit(1)


    # --- Callback Functions ---
    def on_user_transcript(transcript: str):
        """
        This function is called when the user's speech is transcribed.
        """
        print(f"User: {transcript}")

    def on_agent_response(response: str):
        """
        This function is called when the agent provides a response.
        """
        print(f"Agent: {response}")

    def on_conversation_end(conversation_id: str, full_transcript: list):
        """
        This function is called when the conversation ends. It receives the
        full transcript, which is then processed for feedback and saved.
        """
        print(f"\n✅ Conversation {conversation_id} has ended.")
        
        # Define the filename for the transcript
        transcript_filename = f"{conversation_id}_transcript.txt"
        
        print(f"💾 Saving full transcript to: {transcript_filename}")

        # Save the transcript to a file for your feedback mechanism
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
    print("🚀 Starting conversation with ElevenLabs Agent...")
    print("Speak into your microphone. Press Ctrl+C to end the conversation.")
    
    # Initialize the conversation object with all callbacks
    conversation = Conversation(
        client=client,
        agent_id=agent_id,
        callback_user_transcript=on_user_transcript,
        callback_agent_response=on_agent_response,
        callback_on_end=on_conversation_end,
    )

    try:
        # Start the conversation. This will capture audio from your microphone.
        conversation.start()
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        print("\n🛑 Conversation interrupted by user. Shutting down...")
        conversation.stop()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        conversation.stop()

if __name__ == "__main__":
    main()
