import asyncio

from app.services.conversation import ConversationService


async def main():
    conversation = ConversationService()

    print("\n✈️ Tripzy")
    print("Your AI travel planning assistant.")
    print("Tell me about the trip you're planning.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in {"exit", "quit"}:
            print("\nTripzy: Safe travels! ✈️")
            break

        response = await conversation.process_message(user_message)

        print(f"\nTripzy: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())