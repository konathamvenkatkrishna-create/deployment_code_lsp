from core.config import settings
from providers.mock_provider import MockESignProvider
from providers.emudhra_provider import EmudhraProvider


def get_esign_provider():
    """
    Factory to load the correct eSign provider implementation.
    """

    env = settings.ENV.upper()
    provider = settings.ESIGN_PROVIDER.lower()

    # Development environment → mock provider
    if env == "DEV":
        return MockESignProvider()

    # Production providers
    if provider == "emudhra":
        return EmudhraProvider()

    # Future providers
    # elif provider == "nsdl":
    #     return NSDLProvider()

    # elif provider == "digio":
    #     return DigioProvider()

    raise ValueError(f"Unsupported eSign provider: {provider}")