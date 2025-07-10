import gi

try:
    gi.require_version("EDataServer", "1.2")
    print("EDataServer 1.2 namespace found.")
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
