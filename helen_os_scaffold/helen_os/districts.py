from typing import Dict, Any

class District:
    def __init__(self, name: str, code: str):
        self.name = name
        self.code = code

    def get_context(self) -> str:
        return f"Current District: {self.name} ({self.code})"

class OracleTown(District):
    def __init__(self):
        super().__init__("Oracle Town", "OT-01")

    def get_context(self) -> str:
        return super().get_context() + "\nJurisdiction: Constitutional Sovereign. Invariant: No receipt -> no ship."

class DistrictManager:
    def __init__(self):
        self.districts = {
            "oracle_town": OracleTown()
        }

    def get_district(self, name: str) -> District:
        return self.districts.get(name.lower(), District("General", "G-00"))
