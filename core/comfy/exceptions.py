class ComfyUIError(Exception):
    """Custom exception for ComfyUI related errors."""

    def __init__(self, message, status_code=None, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

    def __str__(self):
        return f"ComfyUIError(status={self.status_code}): {super().__str__()} {self.details or ''}"
