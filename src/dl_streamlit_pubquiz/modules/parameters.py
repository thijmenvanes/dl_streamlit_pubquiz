import os
from typing import List, Tuple, Type
from dotenv import find_dotenv
from pydantic_settings import BaseSettings
from pydantic_settings import PydanticBaseSettingsSource

from pondl.parameters.extra_dotenv_settings_source import ExtraDotEnvSettingsSource
from pondl.parameters.parameter_store_settings_source import ParameterStoreSettingsSource


class Parameters(BaseSettings):
    """
    A class to manage the configuration parameters for an application.

    This class inherits from BaseSettings, utilizing Pydantic for environment management. It is designed to
    load configuration parameters from various sources, including environment variables, .env files, and
    AWS Systems Manager Parameter Store, with a defined order of precedence.

    The class supports loading and overriding settings from environment variables and AWS Parameter Store paths
    with an emphasis on secure handling of sensitive information like passwords and private keys.
    """
    # TODO: Add parameters like below
    # example_environment_variable: str

    class Config:
        """Configuration class for the `Parameters` settings.

        Attributes:
        parameter_store_paths (List[str]): List of paths to search for
            parameters in the SSM Parameter Store. The first path has the
            highest priority. Defaults to `os.environ.get('PARAMETER_STORE_PATH')`.
        extra (str): Specifies how to handle extra fields in the configuration.
            Set to "ignore".
        env_file (str): Path to the environment file. This is determined by the
            `find_dotenv()` function.
        env_file_encoding (str): Encoding used for the environment file.
            Defaults to "utf-8".
        extra_env_file_path (str): Path to an additional environment file.
            Defaults to "~/pon_datalab/env_vars/data-science.env".
        extra_env_file_encoding (str): Encoding used for the additional
            environment file. Defaults to "utf-8".
        """
        extra = "ignore"
        env_file = find_dotenv()
        env_file_encoding = "utf-8"

        extra_env_file_path = os.path.join("~/pon_datalab/env_vars", "data-science.env")
        extra_env_file_encoding = "utf-8"

        # Ordered py priority (first path = most important)
        parameter_store_paths: List[str] = [os.environ.get("PARAMETER_STORE_PATH",
                                                           f"/dl_streamlit_pubquiz/"
                                                           f"{os.environ.get('ENVIRONMENT', 'dev')}/")]

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Class Method that returns the prioritized source configuration.

        The environment variables and files/vars with secrets are given
        the highest priority, followed by the
        settings passed during initialization. Finally, the parameters
        retrieved from the SSM Parameter Store
        are given the least priority.

        Args:
            cls: The `Parameters` class.
            settings_cls: The Pydantic settings class.
            init_settings: The configuration parameters passed during
            initialization.
            env_settings: The configuration parameters read from the
            environment variables and files/vars with secrets.
            file_secret_settings: The configuration parameters read from
            the files/vars with secrets.

        Returns:
            Tuple[PydanticBaseSettingsSource, ...]: A tuple containing the
            configuration parameters from different sources in order of priority.
        """
        return (
            env_settings,
            file_secret_settings,
            dotenv_settings,
            ExtraDotEnvSettingsSource(settings_cls),
            init_settings,
            ParameterStoreSettingsSource(settings_cls),
        )


parameters = Parameters()
