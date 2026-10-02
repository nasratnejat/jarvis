from app.memory.manager import memory_manager


USER_ID = "d1dac507-a973-4b24-a027-217a73e4beed"


print("Saving test memory...")

saved = memory_manager.save_memory(
    user_id=USER_ID,
    category="test",
    key="favorite_browser",
    value="Chrome",
    importance=5,
)

print("Saved:")
print(saved)


print("\nReading test memory...")

memory = memory_manager.get_memory(
    user_id=USER_ID,
    key="favorite_browser",
)

print("Retrieved:")
print(memory)