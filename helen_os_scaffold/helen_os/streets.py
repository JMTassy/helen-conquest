from typing import Dict, Any

class Street:
    def __init__(self, name: str, focus: str):
        self.name = name
        self.focus = focus

    def get_context(self) -> str:
        return f"Operational Street: {self.name} | Focus: {self.focus}"

class MarketingStreet(Street):
    def __init__(self):
        super().__init__("Marketing Street", "Narrative creation, brand equity, and social capital.")

    def get_context(self) -> str:
        return super().get_context() + "\nProtocol: Filtered Community & Celebrity Endorsement."

class StreetManager:
    def __init__(self):
        self.streets = {
            "marketing": MarketingStreet()
        }

    def get_street(self, name: str) -> Street:
        return self.streets.get(name.lower(), Street("Main Street", "General Operations"))
