from enum import Enum


class FiefTypeWebhook(Enum):
    """
    Enum class for Fief webhook types.

    Attributes:
        USER_CREATED (str): Webhook type for user creation.
        USER_UPDATED (str): Webhook type for user update.
        USER_DELETED (str): Webhook type for user deletion.
    """

    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
