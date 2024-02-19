from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mail_address: str
    mail_application_password: str
    mail_server: str

    # TODO 環境毎に読み込む.envファイルを切り替える用にする
    model_config = SettingsConfigDict(env_file=".env")
