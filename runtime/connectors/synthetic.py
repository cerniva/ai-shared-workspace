class SyntheticConnector:
    def execute(self, operation: str, params):
        if operation != "echo":
            raise ValueError("unsupported synthetic operation")
        return {"summary": str(params.get("message", ""))}
